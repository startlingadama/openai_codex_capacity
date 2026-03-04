from __future__ import annotations

from datetime import datetime

from fastapi import Header, HTTPException

from backend.app.core.security import (
    generate_token,
    hash_password,
    hash_token,
    token_expiry_iso,
    utc_now_iso,
    verify_password,
)
from backend.app.repositories import auth_repo


def register_user(username: str, password: str, role: str) -> dict:
    if auth_repo.get_user_by_username(username):
        raise HTTPException(status_code=409, detail="Username already exists")

    salt, pw_hash = hash_password(password)
    user_id = auth_repo.create_user(username, role, salt, pw_hash, utc_now_iso())
    token = generate_token()
    auth_repo.create_session(hash_token(token), user_id, token_expiry_iso(), utc_now_iso())
    return {"token": token, "user_id": user_id, "username": username, "role": role}


def login_user(username: str, password: str, rotate_from_token: str | None = None) -> dict:
    row = auth_repo.get_user_by_username(username)
    if not row or not verify_password(password, row["salt"], row["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if rotate_from_token:
        auth_repo.delete_session(hash_token(rotate_from_token))

    token = generate_token()
    auth_repo.create_session(hash_token(token), row["id"], token_expiry_iso(), utc_now_iso())
    return {"token": token, "user_id": row["id"], "username": row["username"], "role": row["role"]}


def _extract_token(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    return authorization.split(" ", 1)[1].strip()


def current_user(authorization: str | None = Header(default=None)) -> dict:
    token = _extract_token(authorization)
    row = auth_repo.get_session_user(hash_token(token))
    if not row:
        raise HTTPException(status_code=401, detail="Invalid token")

    expiry = datetime.fromisoformat(row["expires_at"])
    if expiry < datetime.now(expiry.tzinfo):
        raise HTTPException(status_code=401, detail="Expired token")
    return {"id": row["id"], "username": row["username"], "role": row["role"], "token": token}


def logout_user(token: str) -> None:
    auth_repo.delete_session(hash_token(token))
