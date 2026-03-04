import importlib
import os

import pytest

fastapi = pytest.importorskip("fastapi")
pytest.importorskip("httpx")
from fastapi.testclient import TestClient


def _build_client(tmp_path):
    os.environ["APP_DB_PATH"] = str(tmp_path / "app.sqlite")
    os.environ["RAG_DB_PATH"] = str(tmp_path / "rag.sqlite")
    import backend.app.main as main_module

    importlib.reload(main_module)
    return TestClient(main_module.app)


def test_auth_chat_history_flow(tmp_path):
    client = _build_client(tmp_path)

    register = client.post(
        "/api/auth/register",
        json={"username": "alice", "password": "password123", "role": "user"},
    )
    assert register.status_code == 200
    token = register.json()["token"]

    chat = client.post(
        "/api/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "J'ai un incident urgent"},
    )
    assert chat.status_code == 200
    conversation_id = chat.json()["conversation_id"]

    listing = client.get("/api/conversations", headers={"Authorization": f"Bearer {token}"})
    assert listing.status_code == 200
    assert any(item["id"] == conversation_id for item in listing.json())

    details = client.get(f"/api/conversations/{conversation_id}", headers={"Authorization": f"Bearer {token}"})
    assert details.status_code == 200
    assert len(details.json()["messages"]) >= 2


def test_logout_revokes_token(tmp_path):
    client = _build_client(tmp_path)

    reg = client.post(
        "/api/auth/register",
        json={"username": "bob", "password": "password123", "role": "user"},
    )
    token = reg.json()["token"]

    out = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert out.status_code == 200

    denied = client.get("/api/conversations", headers={"Authorization": f"Bearer {token}"})
    assert denied.status_code == 401
