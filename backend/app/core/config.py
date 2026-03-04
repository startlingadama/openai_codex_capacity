from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class Settings:
    app_env: str = os.getenv("APP_ENV", "development")
    gemini_api_key: str | None = os.getenv("GEMINI_API_KEY")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    rag_db_path: str = os.getenv("RAG_DB_PATH", "backend/data/cdg_rag.sqlite")
    app_db_path: str = os.getenv("APP_DB_PATH", "backend/data/app.sqlite")

    @property
    def allowed_origins(self) -> list[str]:
        raw = os.getenv("ALLOWED_ORIGINS")
        if raw:
            return [item.strip() for item in raw.split(",") if item.strip()]
        if self.app_env == "development":
            return [
                "http://localhost:5173",
                "http://127.0.0.1:5173",
                "http://localhost:3000",
                "http://127.0.0.1:3000",
            ]
        return []


settings = Settings()
