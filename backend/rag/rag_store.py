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
