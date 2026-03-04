# Agent de support conversationnel CDG

Prototype full-stack pour un agent conversationnel orienté support CDG :

- **Backend Python (FastAPI)** : chat, auth, historique, routage support, recherche RAG.
- **LLM Gemini (optionnel)** : génération de réponse enrichie si `GEMINI_API_KEY` est défini.
- **Frontend React** : chatbot flottant responsive, extensible à 1/2 écran.
- **Pipeline RAG** : scraping CDG + index SQLite FTS5.

## Structure

- `backend/` API FastAPI + scripts RAG
- `frontend/` app React
- `backend/data/cdg_rag.sqlite` base locale RAG (générée localement, non versionnée Git)
- `backend/data/app.sqlite` base applicative (users/sessions/conversations/messages)

## Démarrage rapide

### 1) Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export GEMINI_API_KEY="<votre_cle_api>"   # optionnel
uvicorn app.main:app --reload --port 8000
```

### 2) Construire la base RAG (scraping CDG)

```bash
cd ..
python3 -m backend.rag.build_rag_db --start-url https://www.cdgcapitalgestion.ma --max-pages 35
```

### 3) Frontend

```bash
cd frontend
python3 -m http.server 5173
```

## Endpoints

### Auth
- `POST /api/auth/register`
- `POST /api/auth/login`

### Chat & RAG
- `GET /health`
- `POST /api/chat` *(Bearer token requis)*
- `POST /api/rag/search` *(Bearer token requis)*

### Historisation
- `GET /api/conversations` *(Bearer token requis)*
- `GET /api/conversations/{conversation_id}` *(Bearer token requis)*

## Fonctionnalités demandées

- ✅ Brancher un LLM (Gemini) : intégré en mode optionnel, fallback règle métier si indisponible.
- ✅ Ajouter authentification agents/utilisateurs : endpoints register/login + session token.
- ✅ Historisation des conversations : stockage SQLite des conversations et messages.
- ✅ Routage intelligent vers catégories de support : catégorisation `authentication`, `incident`, `product_info`, `general`.
