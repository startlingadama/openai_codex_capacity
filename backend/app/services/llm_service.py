from __future__ import annotations

import json
from urllib.request import Request, urlopen

from backend.app.core.config import settings
from backend.app.core.observability import latency_metric

GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"


def gemini_available() -> bool:
    return bool(settings.gemini_api_key)


def generate_with_gemini(prompt: str) -> str | None:
    if not settings.gemini_api_key:
        return None

    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 500},
    }
    req = Request(
        GEMINI_ENDPOINT.format(model=settings.gemini_model, key=settings.gemini_api_key),
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with latency_metric("llm.gemini.generate", model=settings.gemini_model):
            with urlopen(req, timeout=25) as response:
                payload = json.loads(response.read().decode("utf-8"))
        candidates = payload.get("candidates", [])
        if not candidates:
            return None
        parts = candidates[0].get("content", {}).get("parts", [])
        text = "\n".join(part.get("text", "") for part in parts).strip()
        return text or None
    except Exception:
        return None
