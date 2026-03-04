from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    conversation_id: int | None = None


class ChatResponse(BaseModel):
    reply: str
    sources: list[dict] = Field(default_factory=list)
    category: str
    conversation_id: int


class ConversationSummary(BaseModel):
    id: int
    category: str
    updated_at: str


class ConversationMessage(BaseModel):
    role: str
    content: str
    created_at: str


class ConversationDetails(BaseModel):
    id: int
    category: str
    messages: list[ConversationMessage]
