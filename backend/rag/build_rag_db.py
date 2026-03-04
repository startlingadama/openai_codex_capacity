from __future__ import annotations

import argparse
import json
import ssl
from datetime import datetime, timezone
from collections import deque
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from backend.app.services.rag_service import upsert_embeddings_for_all_chunks
from backend.rag.rag_store import Chunk, init_db, record_ingestion, replace_chunks
from backend.rag.rag_store import Chunk, init_db, replace_chunks


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._in_script = False
        self._in_style = False
        self._title = ""
        self._capture_title = False
        self.links: set[str] = set()
        self.text_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs):
        attrs_dict = dict(attrs)
        if tag == "script":
            self._in_script = True
        if tag == "style":
            self._in_style = True
        if tag == "title":
            self._capture_title = True
        if tag == "a" and "href" in attrs_dict:
            self.links.add(attrs_dict["href"])

    def handle_endtag(self, tag: str):
        if tag == "script":
            self._in_script = False
        if tag == "style":
            self._in_style = False
        if tag == "title":
            self._capture_title = False

    def handle_data(self, data: str):
        if self._in_script or self._in_style:
            return
        text = " ".join(data.split())
        if not text:
            return
        if self._capture_title:
            self._title += f" {text}"
        else:
            self.text_parts.append(text)

    @property
    def title(self) -> str:
        return self._title.strip()

    @property
    def text(self) -> str:
        return " ".join(self.text_parts)


def fetch(url: str, timeout: int = 20) -> str:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    ctx = ssl.create_default_context()
    with urlopen(req, timeout=timeout, context=ctx) as response:
        return response.read().decode("utf-8", errors="ignore")


def same_domain(url: str, root_netloc: str) -> bool:
    return urlparse(url).netloc == root_netloc


def normalize_url(base: str, href: str) -> str | None:
    joined = urljoin(base, href)
    p = urlparse(joined)
    if p.scheme not in {"http", "https"}:
        return None
    return joined.split("#", 1)[0]


def chunk_text(text: str, size: int = 900, overlap: int = 150) -> list[str]:
    words = text.split()
    if not words:
        return []
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + size, len(words))
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start = max(0, end - overlap)
    return chunks


def crawl_site(start_url: str, max_pages: int) -> tuple[list[tuple[str, str, str]], list[str]]:
    root = urlparse(start_url).netloc
    queue = deque([start_url])
    visited: set[str] = set()
    pages: list[tuple[str, str, str]] = []
    errors: list[str] = []

    while queue and len(visited) < max_pages:
        url = queue.popleft()
        if url in visited:
            continue
        visited.add(url)
        try:
            html = fetch(url)
        except Exception as exc:
            errors.append(f"{url} -> {exc}")
            continue

        parser = PageParser()
        parser.feed(html)
        text = parser.text
        if len(text.split()) > 40:
            pages.append((url, parser.title or url, text))

        for href in parser.links:
            normalized = normalize_url(url, href)
            if not normalized:
                continue
            if same_domain(normalized, root) and normalized not in visited:
                queue.append(normalized)

    return pages, errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape CDG Capital Gestion and build a local RAG DB")
    parser.add_argument("--start-url", default="https://www.cdgcapitalgestion.ma")
    parser.add_argument("--max-pages", type=int, default=35)
    parser.add_argument("--db-path", default="backend/data/cdg_rag.sqlite")
    parser.add_argument("--export-json", default="backend/data/cdg_scraped_pages.json")
    args = parser.parse_args()

    pages, errors = crawl_site(args.start_url, args.max_pages)
    chunks: list[Chunk] = []

    for url, title, text in pages:
        for part in chunk_text(text):
            chunks.append(Chunk(url=url, title=title, content=part))

    db_path = Path(args.db_path)
    init_db(db_path)
    total = replace_chunks(db_path, chunks)
    version = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    record_ingestion(db_path, version=version, pages=pages, chunks_count=total)
    embedded = upsert_embeddings_for_all_chunks(db_path)

    export_path = Path(args.export_json)
    export_path.parent.mkdir(parents=True, exist_ok=True)
    export_path.write_text(
        json.dumps(
            [{"url": u, "title": t, "excerpt": txt[:350]} for u, t, txt in pages],
            ensure_ascii=False,
            indent=2,
        )
    )

    print(f"Pages scrapées: {len(pages)}")
    print(f"Chunks indexés: {total}")
    print(f"DB: {db_path}")
    print(f"Embeddings calculés: {embedded}")
    if errors:
        print("Erreurs scraping (3 max):")
        for err in errors[:3]:
            print(f"- {err}")


if __name__ == "__main__":
    main()
