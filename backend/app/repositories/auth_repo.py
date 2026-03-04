from __future__ import annotations

from backend.app.repositories.db import get_conn


def get_user_by_username(username: str):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()


def create_user(username: str, role: str, salt: str, password_hash: str, created_at: str) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO users(username, role, salt, password_hash, created_at) VALUES (?, ?, ?, ?, ?)",
            (username, role, salt, password_hash, created_at),
        )
        conn.commit()
        return cur.lastrowid


def create_session(token_hash: str, user_id: int, expires_at: str, created_at: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO sessions(token_hash, user_id, expires_at, created_at) VALUES (?, ?, ?, ?)",
            (token_hash, user_id, expires_at, created_at),
        )
        conn.commit()


def get_session_user(token_hash: str):
    with get_conn() as conn:
        return conn.execute(
            """
            SELECT s.token_hash, s.expires_at, u.id, u.username, u.role
            FROM sessions s
            JOIN users u ON u.id = s.user_id
            WHERE s.token_hash = ?
            """,
            (token_hash,),
        ).fetchone()


def delete_session(token_hash: str) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash,))
        conn.commit()
