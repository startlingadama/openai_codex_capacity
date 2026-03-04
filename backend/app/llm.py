from __future__ import annotations

import json
import os
from urllib.request import Request, urlopen

GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"


def gemini_available() -> bool:
    return bool(os.getenv("GEMINI_API_KEY"))


def generate_with_gemini(prompt: str, model: str = "gemini-1.5-flash") -> str | None:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None

    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 500},
    }
    data = json.dumps(body).encode("utf-8")
    endpoint = GEMINI_ENDPOINT.format(model=model, key=api_key)

    req = Request(
        endpoint,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
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
