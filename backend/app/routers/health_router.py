from fastapi import APIRouter

from backend.app.services.llm_service import gemini_available

router = APIRouter(tags=["health"])


@router.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok", "gemini": "enabled" if gemini_available() else "disabled"}
