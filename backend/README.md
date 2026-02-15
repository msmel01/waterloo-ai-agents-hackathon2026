# Backend

Backend for **Valentine Hotline**
Voice AI Hackathon Waterloo 2026

This service powers:

- `/api/v1` REST endpoints (public + dashboard)
- Live voice interview orchestration
- async transcript scoring + maintenance jobs

## Stack

- Python 3.11
- FastAPI
- SQLModel + SQLAlchemy
- Alembic
- Redis + arq
- LiveKit agent runtime
- Smallest.ai STT/TTS for low-latency speech pipeline
- OpenAI (conversation) + Anthropic (scoring)

## Why It’s Cool

- Voice-native screening flow with production-style endpoint hardening
- Ultra-efficient speech loop powered by Smallest.ai
- Worker-based scoring pipeline with retry and recovery paths
- Built to be observable, testable, and deployable on Render

## Run Local

1. API

```bash
cd backend
uv sync
uv run uvicorn src.main:app --reload
```

2. Agent (new terminal)

```bash
cd backend
uv run python -m livekit.agents start agent.main
```

3. Worker (new terminal)

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

- Copy `.env.example` -> `.env`
- Set DB, Redis, LiveKit, OpenAI, Anthropic, Clerk keys

## Important Paths

- `src/` -> API + services + repositories
- `agent/` -> voice interview agent
- `workers/` -> scoring + cron jobs
- `migrations/` -> Alembic revisions
