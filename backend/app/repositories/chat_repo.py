from __future__ import annotations

from backend.app.repositories.db import get_conn


def create_conversation(user_id: int, category: str, now: str) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO conversations(user_id, category, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (user_id, category, now, now),
        )
        conn.commit()
        return cur.lastrowid


def get_conversation_for_user(conversation_id: int, user_id: int):
    with get_conn() as conn:
        return conn.execute(
            "SELECT id, category FROM conversations WHERE id = ? AND user_id = ?",
            (conversation_id, user_id),
        ).fetchone()


def update_conversation(conversation_id: int, category: str, now: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE conversations SET category = ?, updated_at = ? WHERE id = ?",
            (category, now, conversation_id),
        )
        conn.commit()


def add_message(conversation_id: int, role: str, content: str, created_at: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO messages(conversation_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (conversation_id, role, content, created_at),
        )
        conn.commit()


def list_conversations(user_id: int):
    with get_conn() as conn:
        return conn.execute(
            "SELECT id, category, updated_at FROM conversations WHERE user_id = ? ORDER BY updated_at DESC",
            (user_id,),
        ).fetchall()


def list_messages(conversation_id: int):
    with get_conn() as conn:
        return conn.execute(
            "SELECT role, content, created_at FROM messages WHERE conversation_id = ? ORDER BY id",
            (conversation_id,),
        ).fetchall()
