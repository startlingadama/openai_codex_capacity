from __future__ import annotations

CATEGORIES = {
    "authentication": ["mot de passe", "password", "connexion", "login", "compte"],
    "incident": ["incident", "bug", "erreur", "bloqué", "panne", "urgent"],
    "product_info": ["opcvm", "fonds", "souscription", "rachat", "tarif", "frais"],
    "general": [],
}


def classify_support_category(message: str) -> str:
    text = message.lower()
    for category, keywords in CATEGORIES.items():
        if any(keyword in text for keyword in keywords):
            return category
    return "general"
