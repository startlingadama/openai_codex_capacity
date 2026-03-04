from fastapi import APIRouter, Depends, HTTPException

from backend.app.repositories import chat_repo
from backend.app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ConversationDetails,
    ConversationMessage,
    ConversationSummary,
)
from backend.app.services.auth_service import current_user
from backend.app.services.chat_service import process_chat

router = APIRouter(tags=["chat"])


@router.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, user=Depends(current_user)):
    try:
        return process_chat(user["id"], payload.message, payload.conversation_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/api/conversations", response_model=list[ConversationSummary])
def list_conversations(user=Depends(current_user)):
    rows = chat_repo.list_conversations(user["id"])
    return [ConversationSummary(id=r["id"], category=r["category"], updated_at=r["updated_at"]) for r in rows]


@router.get("/api/conversations/{conversation_id}", response_model=ConversationDetails)
def get_conversation(conversation_id: int, user=Depends(current_user)):
    conv = chat_repo.get_conversation_for_user(conversation_id, user["id"])
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    rows = chat_repo.list_messages(conversation_id)
    return ConversationDetails(
        id=conv["id"],
        category=conv["category"],
        messages=[ConversationMessage(role=r["role"], content=r["content"], created_at=r["created_at"]) for r in rows],
    )
