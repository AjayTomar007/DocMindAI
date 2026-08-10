# DocMind AI

Upload PDFs, ask questions about them, get answers grounded in your own documents — with sources cited, streamed token-by-token, and saved as reopenable conversations.

## Architecture

```mermaid
flowchart LR
    Browser -->|HTTP + SSE| FastAPI
    FastAPI -->|SQLAlchemy| PG[(Postgres + pgvector)]
    FastAPI -->|enqueue task| Redis[(Redis)]
    Redis --> Worker[Celery Worker]
    Worker -->|extract, chunk| PG
    Worker -->|embed chunks| OpenAI[OpenAI API]
    FastAPI -->|embed query, generate answer| OpenAI
```

**Upload → searchable, end to end:**

```mermaid
sequenceDiagram
    participant U as User
    participant W as FastAPI
    participant Q as Redis
    participant C as Celery Worker
    participant DB as Postgres
    participant AI as OpenAI

    U->>W: POST /upload (PDF)
    W->>DB: save Document (status=queued)
    W-->>U: 303 redirect (immediate)
    W->>Q: enqueue extract_text_task
    Q->>C: deliver task
    C->>DB: extract text (pypdf) -> status=extracted
    C->>C: chunk_text() (word-based, overlapping)
    C->>AI: embed chunks (batched)
    C->>DB: store DocumentChunk rows -> status=processed
```

**Asking a question:**

```mermaid
sequenceDiagram
    participant U as User
    participant W as FastAPI
    participant DB as Postgres
    participant AI as OpenAI

    U->>W: POST /chat/message
    W->>DB: save user Message, create Conversation if new
    W-->>U: bootstrap fragment (opens SSE connection)
    U->>W: GET /chat/stream (SSE)
    W->>AI: embed question
    W->>DB: cosine_distance search, top-k chunks
    W->>AI: stream chat completion (context + question)
    AI-->>W: token deltas
    W-->>U: SSE data events (typing effect)
    W->>DB: save assistant Message + sources
```

## Tech stack

- **Backend**: Python 3.13, FastAPI, SQLAlchemy, Alembic, Pydantic
- **AI**: OpenAI (embeddings + chat completions), pgvector
- **Database**: PostgreSQL + pgvector extension
- **Background jobs**: Redis + Celery
- **Storage**: local filesystem
- **Frontend**: Jinja2 + Bootstrap 5 + HTMX (incl. `htmx-ext-sse` for streaming) — no React, no build step
- **PDF extraction**: pypdf

## Features

- PDF upload with background processing (extraction → chunking → embedding), live status shown in the UI without a page refresh
- Semantic search over document chunks via pgvector cosine similarity
- RAG: retrieved chunks feed an LLM prompt; answers cite their source documents
- Streamed answers over Server-Sent Events (token-by-token, no polling)
- Persistent, reopenable, multi-conversation chat history
- Rate limiting, structured logging, a `/health` endpoint, and friendly (HTMX-aware) error pages

## Project structure

```
docmind-ai/
  app/
    api/          # route handlers (pages, documents, chat, health)
    core/         # config, templates, logging, rate limiting
    db/           # SQLAlchemy engine/session/base
    models/       # ORM models
    schemas/      # Pydantic schemas
    services/     # business logic (one concern per file)
    workers/      # Celery app + tasks
    templates/    # Jinja2 templates (+ partials/ for HTMX fragments)
    static/       # CSS
  alembic/        # migrations
  main.py
  requirements.txt
  Dockerfile
  docker-compose.yml
```

## Running locally (native, no Docker)

This is how the project was actually developed — full control, fast iteration, no container overhead.

**Prerequisites**: Python 3.13 (via `pyenv`), [Postgres.app](https://postgresapp.com/) (PG17, with `pgvector` built against it), Redis (built from source into `~/redis`), an OpenAI API key.

```bash
# 1. Virtualenv + deps
cd docmind-ai
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Configure
cp .env.example .env   # then fill in OPENAI_API_KEY

# 3. Database
alembic upgrade head

# 4. Run everything (4 separate processes)
# Postgres.app should already be running (or start it via its GUI / pg_ctl)
~/redis/bin/redis-server --daemonize yes --port 6379 --bind 127.0.0.1 --dir ~/redis/data --save ""
celery -A app.workers.celery_app worker --loglevel=info &
uvicorn main:app --reload
```

Then open http://127.0.0.1:8000.

## Running with Docker

```bash
cd docmind-ai
cp .env.example .env   # fill in OPENAI_API_KEY
docker compose up --build
```

This starts four containers: `db` (Postgres + pgvector), `redis`, `app` (FastAPI, runs migrations on startup), and `worker` (Celery). The app is available at http://localhost:8000.

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg://docmind:docmind@localhost:5432/docmind` | Postgres connection string |
| `STORAGE_DIR` | `storage/uploads` | Where uploaded PDFs are saved locally |
| `CELERY_BROKER_URL` | `redis://127.0.0.1:6379/0` | Redis DB used as the Celery task queue |
| `CELERY_RESULT_BACKEND` | `redis://127.0.0.1:6379/1` | Redis DB used for Celery task results |
| `REDIS_URL` | `redis://127.0.0.1:6379/2` | Redis DB used for rate limiting |
| `OPENAI_API_KEY` | *(empty)* | **Required** for embeddings/chat to work |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model |
| `OPENAI_CHAT_MODEL` | `gpt-4o-mini` | Chat completion model |
| `EMBEDDING_DIM` | `1536` | Must match the embedding model's output dimension |
| `RATE_LIMIT_PER_MINUTE` | `20` | Per-IP, per-route request cap |

## Health check

`GET /health` returns `{"status": "ok", "database": "ok", "redis": "ok"}` (200), or `"degraded"` with the failing component marked `"error"` (503).
