# Frontend

Frontend app for **Valentine Hotline** (Voice AI Hackathon Waterloo - 2026).

## Tech Stack

- React
- TypeScript
- Vite
- Tailwind CSS
- TanStack Query
- LiveKit client SDK
- Clerk (auth)

## Run Locally

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

Create `frontend/.env.local` and set values like:

- `VITE_API_URL` (example: `http://localhost:8000`)
- `VITE_CLERK_PUBLISHABLE_KEY`
- `VITE_HEART_SLUG` (example: `heart`)

## Key Paths

- `src/pages/` — route screens
- `src/components/` — UI components
- `src/hooks/` — app hooks (auth, polling, LiveKit)
- `src/api/` — API client + generated endpoints
- `src/types/` — shared frontend types

## Notes

- API calls target backend `/api/v1` routes.
- Interview room uses LiveKit token returned by backend session start endpoint.
