# Valentine Hotline

Built for **Voice AI Hackathon Waterloo 2026**.

Valentine Hotline is a voice-first AI screening pipeline for dating intros:

`Suitor calls in -> AI interview -> transcript + scoring -> Date / No Date`

## Why It Feels Fast

Valentine Hotline is tuned for ultra-efficient voice interactions using **[Smallest.ai](https://smallest.ai/)** for low-latency speech handling in the interview loop.

## Repo Map

- `backend/` -> FastAPI API, LiveKit agent, async workers
- `frontend/` -> React + Vite app
- `locustfile.py` -> load testing profile
- `render.yaml` -> deployment setup

## Stack

- Backend: FastAPI, SQLModel/SQLAlchemy, Alembic, Redis, arq
- Frontend: React, TypeScript, Vite, Tailwind
- Voice: LiveKit + Smallest.ai STT/TTS + OpenAI conversation engine
- Scoring: Anthropic Claude
- Infra: Neon Postgres + Render

## Quick Start

1. API

```bash
cd backend
uv sync
uv run uvicorn src.main:app --reload
```

2. Voice Agent (new terminal)

```bash
cd backend
uv run python -m livekit.agents start agent.main
```

3. Worker (new terminal)

```bash
cd backend
uv run arq workers.main.WorkerSettings
```

4. Frontend

```bash
cd frontend
npm install
npm run dev
```

## Environment

- Configure `backend/.env`
- Configure `frontend/.env.local`
- API base path is `/api/v1`

## More Docs

- `backend/README.md`
- `frontend/README.md`
