# Agent de support conversationnel CDG

Prototype full-stack pour un agent conversationnel orienté support CDG :

- **Backend Python (FastAPI)** pour exposer une API de chat.
- **Frontend React** pour une interface de conversation simple.

## Structure

- `backend/` API FastAPI
- `frontend/` app React

## Démarrage rapide

### 1) Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 2) Frontend

```bash
cd frontend
python3 -m http.server 5173
```

Le frontend appelle `http://localhost:8000/api/chat`.

## Exemple requête API

```bash
curl -X POST http://localhost:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"Bonjour, j\'ai un souci de mot de passe"}'
```

## Pistes d'évolution

- Brancher un LLM (OpenAI, Azure OpenAI, etc.)
- Ajouter authentification agents/utilisateurs
- Historisation des conversations
- Routage intelligent vers catégories de support
