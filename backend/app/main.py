from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="CDG Support Conversation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Message utilisateur")


class ChatResponse(BaseModel):
    reply: str


def build_support_reply(user_message: str) -> str:
    msg = user_message.lower()

    if any(keyword in msg for keyword in ["mot de passe", "password", "connexion", "login"]):
        return (
            "Je peux vous aider pour l'accès au compte CDG. "
            "Essayez d'abord la procédure de réinitialisation du mot de passe, "
            "puis vérifiez que votre identifiant est correct. "
            "Si le problème persiste, je peux ouvrir un ticket support."
        )

    if any(keyword in msg for keyword in ["ticket", "incident", "bug", "erreur"]):
        return (
            "Merci pour le signalement. Pour créer un ticket, j'ai besoin de : "
            "1) l'impact métier, 2) un message d'erreur exact, 3) la date/heure, "
            "4) une capture d'écran si possible."
        )

    if any(keyword in msg for keyword in ["bonjour", "salut", "hello"]):
        return (
            "Bonjour 👋 Je suis l'agent de support conversationnel CDG. "
            "Expliquez votre besoin (accès, incident, ticket, etc.) et je vous guide."
        )

    return (
        "J'ai bien reçu votre demande. Pouvez-vous préciser le contexte "
        "(application concernée, action réalisée, résultat attendu) ? "
        "Je vous aiderai à formaliser un ticket CDG complet."
    )


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    return ChatResponse(reply=build_support_reply(payload.message))
