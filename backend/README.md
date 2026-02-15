# Backend

Backend service for **Valentine Hotline** (Voice AI Hackathon Waterloo - 2026).

## What it includes

- FastAPI REST API (`/api/v1`)
- LiveKit voice agent runtime (`agent/`)
- arq worker tasks (`workers/`)
- PostgreSQL models + migrations

## Tech Stack

- Python 3.11
- FastAPI
- SQLAlchemy + SQLModel
- Alembic
- Redis + arq
- LiveKit + Deepgram + OpenAI
- Anthropic Claude (scoring)

## Run Locally

### API

```bash
cd backend
uv sync
uv run uvicorn src.main:app --reload
```

### Agent (new terminal)

```bash
cd backend
uv run python -m livekit.agents start agent.main
```

### Worker (new terminal)

```bash
cd backend
uv run arq workers.main.WorkerSettings
```

## Migrations

```bash
cd backend
uv run alembic upgrade head
```

## Tests

```bash
cd backend
uv run pytest -v
```

## Environment

- Copy `.env.example` to `.env`
- Fill required keys for DB, LiveKit, Deepgram, OpenAI, Anthropic, Clerk, Redis

## Key Paths

- `src/` — API, schemas, services, repositories
- `agent/` — LiveKit interview agent
- `workers/` — scoring + maintenance jobs
- `migrations/` — Alembic migrations
- `config/heart_config.yaml` — heart persona/questions config
