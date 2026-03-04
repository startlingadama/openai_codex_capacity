from pathlib import Path

from fastapi import APIRouter, Depends

from backend.app.core.config import settings
from backend.app.schemas.rag import RagSearchRequest, RagSearchResponse
from backend.app.services.auth_service import current_user
from backend.app.services.rag_service import search_hybrid

router = APIRouter(prefix="/api/rag", tags=["rag"])
RAG_DB_PATH = Path(settings.rag_db_path)


@router.post("/search", response_model=RagSearchResponse)
def rag_search(payload: RagSearchRequest, user=Depends(current_user)):
    _ = user
    if not RAG_DB_PATH.exists():
        return RagSearchResponse(results=[])
    return RagSearchResponse(results=search_hybrid(RAG_DB_PATH, payload.query, payload.k))
