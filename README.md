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

## Nouvelle configuration (auth + LLM + RAG)

### Variables d'environnement

- `GEMINI_API_KEY` *(optionnel)* : active les réponses Gemini.
- Si la clé est absente/invalide, l'API bascule automatiquement sur le fallback métier.

Exemple :

```bash
export GEMINI_API_KEY="<votre_cle_api_gemini>"
```

### Données locales

- `backend/data/app.sqlite` : créée automatiquement au démarrage du backend.
- `backend/data/cdg_rag.sqlite` : créée via le script de build RAG.
- Les fichiers `.sqlite` sont ignorés par Git (non versionnés).

### Schéma applicatif (SQLite)

La base `app.sqlite` contient :
- `users` : utilisateurs (`agent` ou `user`), hash/salt mot de passe.
- `sessions` : tokens Bearer avec date d'expiration.
- `conversations` : historique de conversations par utilisateur.
- `messages` : messages user/assistant liés à une conversation.
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
export APP_ENV=development
export GEMINI_API_KEY="<optionnel>"
uvicorn app.main:app --reload --port 8000
```

Frontend :
export GEMINI_API_KEY="<votre_cle_api>"   # optionnel
uvicorn app.main:app --reload --port 8000
```

### 2) Construire la base RAG (scraping CDG)

```bash
cd ..
python3 -m backend.rag.build_rag_db --start-url https://www.cdgcapitalgestion.ma --max-pages 35
```

### 3) Frontend
uvicorn app.main:app --reload --port 8000
```

### 2) Frontend

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

### Chat & RAG
- `GET /health`
- `POST /api/chat` *(Bearer token requis)*
- `POST /api/rag/search` *(Bearer token requis)*

### Historisation
- `GET /api/conversations` *(Bearer token requis)*
- `GET /api/conversations/{conversation_id}` *(Bearer token requis)*

## Exemples de configuration API

```bash
# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"username":"demo_user","password":"demo12345","role":"user"}'
```

```bash
# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"demo_user","password":"demo12345"}'
```

```bash
# Chat authentifié
curl -X POST http://localhost:8000/api/chat \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <TOKEN>' \
  -d '{"message":"Je n\'arrive pas à me connecter"}'
```

## Fonctionnalités demandées

- ✅ Brancher un LLM (Gemini) : intégré en mode optionnel, fallback règle métier si indisponible.
- ✅ Ajouter authentification agents/utilisateurs : endpoints register/login + session token.
- ✅ Historisation des conversations : stockage SQLite des conversations et messages.
- ✅ Routage intelligent vers catégories de support : catégorisation `authentication`, `incident`, `product_info`, `general`.
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
