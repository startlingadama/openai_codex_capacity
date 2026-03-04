from __future__ import annotations

import ast
import math
import re
import sqlite3
from pathlib import Path

from backend.app.core.observability import latency_metric

WORD_RE = re.compile(r"\w+", re.UNICODE)
EMBED_DIM = 64


def _tokenize(text: str) -> list[str]:
    return WORD_RE.findall(text.lower())


def _embed_text(text: str, dim: int = EMBED_DIM) -> list[float]:
    vec = [0.0] * dim
    for token in _tokenize(text):
        vec[hash(token) % dim] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def _cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def _ensure_embedding_table(db_path: Path) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chunk_embeddings (
                rowid INTEGER PRIMARY KEY,
                embedding TEXT NOT NULL
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
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                title TEXT,
                version TEXT NOT NULL,
                ingested_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def upsert_embeddings_for_all_chunks(db_path: Path) -> int:
    _ensure_embedding_table(db_path)
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute("SELECT rowid, content FROM chunks_fts").fetchall()
        conn.execute("DELETE FROM chunk_embeddings")
        for rowid, content in rows:
            emb = _embed_text(content)
            conn.execute("INSERT INTO chunk_embeddings(rowid, embedding) VALUES (?, ?)", (rowid, repr(emb)))
        conn.commit()
        return len(rows)


def search_hybrid(db_path: Path, query: str, limit: int = 5) -> list[dict]:
    with latency_metric("rag.search", limit=limit):
        with sqlite3.connect(db_path) as conn:
            fts_rows = conn.execute(
                """
                SELECT rowid, url, title, content
                FROM chunks_fts
                WHERE chunks_fts MATCH ?
                LIMIT ?
                """,
                (" ".join(_tokenize(query)), max(10, limit * 3)),
            ).fetchall()

            q_emb = _embed_text(query)
            scored: list[tuple[float, tuple]] = []
            for row in fts_rows:
                emb_row = conn.execute("SELECT embedding FROM chunk_embeddings WHERE rowid = ?", (row[0],)).fetchone()
                if not emb_row:
                    sim = 0.0
                else:
                    sim = _cosine(q_emb, list(ast.literal_eval(emb_row[0])))
                scored.append((sim, row))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [{"url": r[1], "title": r[2], "content": r[3][:500]} for _, r in scored[:limit]]
