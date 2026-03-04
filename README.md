# Agent de support conversationnel CDG

Architecture refactorisée en couches pour un backend maintenable et testable.

## Architecture backend (Layered)

- `backend/app/routers/` : endpoints FastAPI (auth, chat, rag, health)
- `backend/app/services/` : logique métier (auth, chat, llm, routing, rag)
- `backend/app/repositories/` : accès base SQLite
- `backend/app/schemas/` : modèles Pydantic request/response
- `backend/app/core/` : config, sécurité, observabilité

## Configuration

### Variables d'environnement

- `APP_ENV` : `development` (par défaut) ou `production`
- `ALLOWED_ORIGINS` : liste CSV stricte pour CORS (ex: `https://app.cdg.ma,https://admin.cdg.ma`)
- `APP_DB_PATH` : chemin DB applicative SQLite (default `backend/data/app.sqlite`)
- `RAG_DB_PATH` : chemin DB RAG SQLite (default `backend/data/cdg_rag.sqlite`)
- `GEMINI_API_KEY` : clé Gemini (optionnel)
- `GEMINI_MODEL` : modèle Gemini (default `gemini-1.5-flash`)

### CORS strict par environnement

- En `development`, origines locales autorisées (`localhost:5173`, `localhost:3000`).
- En `production`, aucune origine par défaut : **définir `ALLOWED_ORIGINS` explicitement**.

## Sécurité Auth

- Hash PBKDF2 des mots de passe (`sha256`).
- **Hash SHA256 du token session stocké en DB** (jamais le token brut).
- Login avec rotation possible du token via bearer existant.
- Endpoint `POST /api/auth/logout` pour révocation session.

## RAG v2

- Recherche hybride : FTS5 + embeddings hashés (64 dimensions) + reranking cosine.
- Versionnement ingestion (`documents.version`) + journaux (`ingestion_logs`).
- Script d'ingestion :

```bash
python3 -m backend.rag.build_rag_db --start-url https://www.cdgcapitalgestion.ma --max-pages 35
```

## Observabilité

- Logs structurés JSON (event-based).
- Métriques latence (LLM et RAG search) en ms dans les logs.

## Démarrage rapide

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export APP_ENV=development
export GEMINI_API_KEY="<optionnel>"
uvicorn app.main:app --reload --port 8000
```

Frontend :

```bash
cd frontend
python3 -m http.server 5173
```

## Endpoints

### Auth
- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/logout`

### Chat & RAG
- `GET /health`
- `POST /api/chat` *(Bearer requis)*
- `POST /api/rag/search` *(Bearer requis)*

### Historisation
- `GET /api/conversations` *(Bearer requis)*
- `GET /api/conversations/{conversation_id}` *(Bearer requis)*

## Tests

- Unitaires: sécurité + routage
- API: auth/chat/history/logout

```bash
pytest -q backend/app/tests
```
