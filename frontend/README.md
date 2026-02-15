# Frontend

Frontend for **Valentine Hotline**
Voice AI Hackathon Waterloo 2026

The UI delivers the full suitor + dashboard experience:

- suitor onboarding and interview journey
- real-time voice room UX
- results, feedback, and booking flow
- dashboard analytics + session review

## Stack

- React + TypeScript + Vite
- Tailwind CSS
- TanStack Query
- LiveKit client SDK
- Clerk auth

Interview UX is optimized for fast turn-taking, backed by a Smallest.ai-powered speech pipeline on the backend.

## Run Local

```bash
cd frontend
npm install
npm run dev
```

## Build

```bash
cd frontend
npm run build
```

## Environment

Create `frontend/.env.local`:

- `VITE_API_URL=http://localhost:8000`
- `VITE_CLERK_PUBLISHABLE_KEY=...`
- `VITE_HEART_SLUG=heart`

## Important Paths

- `src/pages/` -> route pages
- `src/components/` -> reusable UI
- `src/hooks/` -> auth, polling, session hooks
- `src/api/` -> axios + generated clients
- `src/types/` -> app types

## Notes

- API target: `/api/v1`
- Session tokens are issued by backend and consumed by LiveKit UI
