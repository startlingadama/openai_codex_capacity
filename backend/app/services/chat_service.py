from __future__ import annotations

from pathlib import Path

from backend.app.core.config import settings
from backend.app.core.observability import log_event
from backend.app.core.security import utc_now_iso
from backend.app.repositories import chat_repo
from backend.app.services.llm_service import generate_with_gemini
from backend.app.services.rag_service import search_hybrid
from backend.app.services.routing_service import classify_support_category

RAG_DB_PATH = Path(settings.rag_db_path)


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
        return "Essayez la réinitialisation du mot de passe puis vérifiez l'identifiant."
    if category == "incident":
        return "Merci de préciser impact, erreur exacte, date/heure et capture d'écran."
    if category == "product_info":
        return "Précisez le produit/fonds concerné pour une réponse ciblée."
    return "Pouvez-vous préciser le contexte (application, action, résultat attendu) ?"


def process_chat(user_id: int, message: str, conversation_id: int | None) -> dict:
    sources = search_hybrid(RAG_DB_PATH, message, 3) if RAG_DB_PATH.exists() else []
    category = classify_support_category(message)
    reply = build_support_reply(message, category, sources)

    now = utc_now_iso()
    if conversation_id is None:
        conversation_id = chat_repo.create_conversation(user_id, category, now)
    else:
        conv = chat_repo.get_conversation_for_user(conversation_id, user_id)
        if not conv:
            raise ValueError("Conversation not found")
        chat_repo.update_conversation(conversation_id, category, now)

    chat_repo.add_message(conversation_id, "user", message, now)
    chat_repo.add_message(conversation_id, "assistant", reply, now)
    log_event("chat.processed", user_id=user_id, conversation_id=conversation_id, category=category)
    return {
        "reply": reply,
        "sources": sources,
        "category": category,
        "conversation_id": conversation_id,
    }
