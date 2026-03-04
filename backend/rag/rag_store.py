from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

WORD_RE = re.compile(r"\w+", re.UNICODE)


@dataclass
class Chunk:
    url: str
    title: str
    content: str


def _tokenize(text: str) -> str:
    return " ".join(WORD_RE.findall(text.lower()))


def init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
                content,
                title,
                url,
                tokenize='unicode61'
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                title TEXT,
                version TEXT NOT NULL,
                ingested_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ingestion_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT NOT NULL,
                pages_count INTEGER NOT NULL,
                chunks_count INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chunk_embeddings (
                rowid INTEGER PRIMARY KEY,
                embedding TEXT NOT NULL
            )
            """
        )
        conn.commit()


def replace_chunks(db_path: Path, chunks: Iterable[Chunk]) -> int:
    with sqlite3.connect(db_path) as conn:
        conn.execute("DELETE FROM chunks_fts")
        count = 0
        for chunk in chunks:
            conn.execute(
                "INSERT INTO chunks_fts(content, title, url) VALUES (?, ?, ?)",
                (_tokenize(chunk.content), chunk.title, chunk.url),
            )
            count += 1
        conn.commit()
        return count


def record_ingestion(db_path: Path, *, version: str, pages: list[tuple[str, str, str]], chunks_count: int) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(db_path) as conn:
        conn.execute("DELETE FROM documents")
        for url, title, _ in pages:
            conn.execute(
                "INSERT INTO documents(url, title, version, ingested_at) VALUES (?, ?, ?, ?)",
                (url, title, version, now),
            )
        conn.execute(
            "INSERT INTO ingestion_logs(version, pages_count, chunks_count, created_at) VALUES (?, ?, ?, ?)",
            (version, len(pages), chunks_count, now),
        )
        conn.commit()


def search(db_path: Path, query: str, limit: int = 5) -> list[dict]:
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT url, title, content
            FROM chunks_fts
            WHERE chunks_fts MATCH ?
            LIMIT ?
            """,
            (_tokenize(query), limit),
        ).fetchall()
    return [{"url": r[0], "title": r[1], "content": r[2][:500]} for r in rows]


def latest_ingestion(db_path: Path) -> dict | None:
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT version, pages_count, chunks_count, created_at FROM ingestion_logs ORDER BY id DESC LIMIT 1"
        ).fetchone()
    if not row:
        return None
    return {
        "version": row[0],
        "pages_count": row[1],
        "chunks_count": row[2],
        "created_at": row[3],
    }
