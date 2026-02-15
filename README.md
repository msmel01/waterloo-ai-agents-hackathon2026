# Valentine Hotline

Project for **Voice AI Hackathon Waterloo - 2026**.

Valentine Hotline is an AI-powered dating screening system where suitors have a voice interview with an AI persona, then receive scored results and a date/no-date verdict.

## Monorepo

- `backend/` — FastAPI API, LiveKit agent runtime, worker tasks
- `frontend/` — React + Vite client app
- `locustfile.py` — load testing entry
- `render.yaml` — deployment blueprint

## Tech Stack

- Backend: Python, FastAPI, SQLAlchemy/SQLModel, Alembic
- Frontend: React, TypeScript, Vite, Tailwind
- Realtime voice: LiveKit + Deepgram + OpenAI
- Scoring: Anthropic Claude via arq worker + Redis
- Database: PostgreSQL (Neon)
- Auth: Clerk (suitor), API key (dashboard)

## Quick Start

### 1) Backend

```bash
cd backend
uv sync
uv run uvicorn src.main:app --reload
```

### 2) Agent (separate terminal)

```bash
cd backend
uv run python -m livekit.agents start agent.main
```

### 3) Worker (separate terminal)

```bash
cd backend
uv run arq workers.main.WorkerSettings
```

### 4) Frontend

```bash
cd frontend
npm install
npm run dev
```

## Notes

- Set environment variables in `backend/.env` and `frontend/.env.local`.
- API is served under `/api/v1`.
- For folder-specific details, see:
  - `backend/README.md`
  - `frontend/README.md`
