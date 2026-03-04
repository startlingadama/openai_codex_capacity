from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import settings
from backend.app.repositories.db import init_db
from backend.app.routers.auth_router import router as auth_router
from backend.app.routers.chat_router import router as chat_router
from backend.app.routers.health_router import router as health_router
from backend.app.routers.rag_router import router as rag_router

app = FastAPI(title="CDG Support Conversation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.on_event("startup")
def startup() -> None:
    init_db()


app.include_router(health_router)
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(rag_router)
