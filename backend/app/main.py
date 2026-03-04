from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.app.llm import generate_with_gemini, gemini_available
from backend.app.routing import classify_support_category
from backend.app.security import generate_token, hash_password, token_expiry_iso, utc_now_iso, verify_password
from backend.app.store import get_conn, init_app_db
from backend.rag.rag_store import search

app = FastAPI(title="CDG Support Conversation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RAG_DB_PATH = Path("backend/data/cdg_rag.sqlite")


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    role: str = Field(default="user", pattern="^(agent|user)$")


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    token: str
    user_id: int
    username: str
    role: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Message utilisateur")
    conversation_id: int | None = None


class ChatResponse(BaseModel):
    reply: str
    sources: list[dict] = []
    category: str
    conversation_id: int


class RagSearchRequest(BaseModel):
    query: str = Field(..., min_length=2)
    k: int = Field(default=5, ge=1, le=10)


class RagSearchResponse(BaseModel):
    results: list[dict]


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


@app.on_event("startup")
def startup() -> None:
    init_app_db()


def _extract_token(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    return authorization.split(" ", 1)[1].strip()


def current_user(authorization: str | None = Header(default=None)) -> dict:
    token = _extract_token(authorization)
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT s.token, s.expires_at, u.id, u.username, u.role
            FROM sessions s
            JOIN users u ON u.id = s.user_id
            WHERE s.token = ?
            """,
            (token,),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="Invalid token")

    expiry = datetime.fromisoformat(row["expires_at"])
    if expiry < datetime.now(expiry.tzinfo):
        raise HTTPException(status_code=401, detail="Expired token")
    return {"id": row["id"], "username": row["username"], "role": row["role"]}


def build_support_reply(user_message: str, category: str, sources: list[dict]) -> str:
    context_block = "\n".join(f"- {s['title']}: {s['content'][:220]}" for s in sources[:3])
    prompt = (
        "Tu es un agent support CDG. Réponds en français de manière concise et professionnelle.\n"
        f"Catégorie: {category}\n"
        f"Message utilisateur: {user_message}\n"
        f"Contexte documentaire: {context_block or 'Aucune source RAG disponible.'}\n"
        "Donne des étapes actionnables."
    )
    llm_reply = generate_with_gemini(prompt)
    if llm_reply:
        return llm_reply

    if category == "authentication":
        return (
            "Je peux vous aider pour l'accès au compte CDG. Essayez d'abord la réinitialisation "
            "du mot de passe puis vérifiez votre identifiant. Si besoin, je peux préparer un ticket."
        )
    if category == "incident":
        return (
            "Merci pour le signalement. Merci de préciser: impact métier, message d'erreur exact, "
            "date/heure et capture d'écran pour accélérer la prise en charge."
        )
    if category == "product_info":
        return "Je peux vous orienter sur les produits/fonds CDG. Précisez le produit concerné et votre besoin."
    return "J'ai bien reçu votre demande. Pouvez-vous préciser le contexte pour un traitement rapide ?"


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok", "gemini": "enabled" if gemini_available() else "disabled"}


@app.post("/api/auth/register", response_model=AuthResponse)
def register(payload: RegisterRequest) -> AuthResponse:
    salt, hashed = hash_password(payload.password)
    now = utc_now_iso()
    with get_conn() as conn:
        exists = conn.execute("SELECT 1 FROM users WHERE username = ?", (payload.username,)).fetchone()
        if exists:
            raise HTTPException(status_code=409, detail="Username already exists")
        cur = conn.execute(
            "INSERT INTO users(username, role, salt, password_hash, created_at) VALUES (?, ?, ?, ?, ?)",
            (payload.username, payload.role, salt, hashed, now),
        )
        user_id = cur.lastrowid
        token = generate_token()
        conn.execute(
            "INSERT INTO sessions(token, user_id, expires_at, created_at) VALUES (?, ?, ?, ?)",
            (token, user_id, token_expiry_iso(), now),
        )
        conn.commit()
    return AuthResponse(token=token, user_id=user_id, username=payload.username, role=payload.role)


@app.post("/api/auth/login", response_model=AuthResponse)
def login(payload: LoginRequest) -> AuthResponse:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (payload.username,)).fetchone()
        if not row or not verify_password(payload.password, row["salt"], row["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        token = generate_token()
        conn.execute(
            "INSERT INTO sessions(token, user_id, expires_at, created_at) VALUES (?, ?, ?, ?)",
            (token, row["id"], token_expiry_iso(), utc_now_iso()),
        )
        conn.commit()
    return AuthResponse(token=token, user_id=row["id"], username=row["username"], role=row["role"])


@app.post("/api/rag/search", response_model=RagSearchResponse)
def rag_search(payload: RagSearchRequest, user=Depends(current_user)) -> RagSearchResponse:
    _ = user
    if not RAG_DB_PATH.exists():
        return RagSearchResponse(results=[])
    return RagSearchResponse(results=search(RAG_DB_PATH, payload.query, payload.k))


@app.get("/api/conversations", response_model=list[ConversationSummary])
def list_conversations(user=Depends(current_user)) -> list[ConversationSummary]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, category, updated_at FROM conversations WHERE user_id = ? ORDER BY updated_at DESC",
            (user["id"],),
        ).fetchall()
    return [ConversationSummary(id=r["id"], category=r["category"], updated_at=r["updated_at"]) for r in rows]


@app.get("/api/conversations/{conversation_id}", response_model=ConversationDetails)
def get_conversation(conversation_id: int, user=Depends(current_user)) -> ConversationDetails:
    with get_conn() as conn:
        conv = conn.execute(
            "SELECT id, category FROM conversations WHERE id = ? AND user_id = ?",
            (conversation_id, user["id"]),
        ).fetchone()
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        rows = conn.execute(
            "SELECT role, content, created_at FROM messages WHERE conversation_id = ? ORDER BY id",
            (conversation_id,),
        ).fetchall()
    return ConversationDetails(
        id=conv["id"],
        category=conv["category"],
        messages=[ConversationMessage(role=r["role"], content=r["content"], created_at=r["created_at"]) for r in rows],
    )


@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, user=Depends(current_user)) -> ChatResponse:
    sources = search(RAG_DB_PATH, payload.message, 3) if RAG_DB_PATH.exists() else []
    category = classify_support_category(payload.message)
    reply = build_support_reply(payload.message, category, sources)

    now = utc_now_iso()
    with get_conn() as conn:
        conversation_id = payload.conversation_id
        if conversation_id is None:
            cur = conn.execute(
                "INSERT INTO conversations(user_id, category, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (user["id"], category, now, now),
            )
            conversation_id = cur.lastrowid
        else:
            owner = conn.execute(
                "SELECT id FROM conversations WHERE id = ? AND user_id = ?",
                (conversation_id, user["id"]),
            ).fetchone()
            if not owner:
                raise HTTPException(status_code=404, detail="Conversation not found")
            conn.execute(
                "UPDATE conversations SET category = ?, updated_at = ? WHERE id = ?",
                (category, now, conversation_id),
            )

        conn.execute(
            "INSERT INTO messages(conversation_id, role, content, created_at) VALUES (?, 'user', ?, ?)",
            (conversation_id, payload.message, now),
        )
        conn.execute(
            "INSERT INTO messages(conversation_id, role, content, created_at) VALUES (?, 'assistant', ?, ?)",
            (conversation_id, reply, now),
        )
        conn.commit()

    return ChatResponse(reply=reply, sources=sources, category=category, conversation_id=conversation_id)
