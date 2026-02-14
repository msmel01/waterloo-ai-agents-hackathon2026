# Valentine Hotline — Frontend

Client UI for a voice-based **Virtual Dating Assistant** — a WebRTC room where a **suitor** joins from the browser (mic access) and an **AI voice agent** (via LiveKit) is the other participant.

## Setup

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

Output directory: `frontend/dist/`

## Environment

| Variable | Description |
|----------|-------------|
| `VITE_LIVEKIT_URL` | LiveKit server URL (e.g. `wss://your-project.livekit.cloud`). Set in `.env` for local dev and in Vercel project settings for production. |
| `VITE_CLERK_PUBLISHABLE_KEY` | Clerk publishable key (from [Clerk Dashboard](https://dashboard.clerk.com) → API Keys). For future auth; not required for current dummy UI. |

## Deployment (Vercel)

- Point Vercel to the `frontend/` directory (or set root directory to `frontend`).
- **Build command:** `npm run build`
- **Output directory:** `dist/`
- Add `VITE_LIVEKIT_URL` and `VITE_CLERK_PUBLISHABLE_KEY` in your Vercel project environment variables.

## Current state (dummy UI)

The app runs a **full dummy UI** with TODO stubs. No login required. With placeholder token/URL, the ScreeningRoom shows demo mode (no real LiveKit connection). Use this to develop the UI while backend APIs are built.

## Token fetching

The app uses a **placeholder token** stub in `src/api/livekitToken.ts`. To connect to a real LiveKit room:

1. Implement a backend endpoint that issues LiveKit access tokens using the [LiveKit Access Token API](https://docs.livekit.io/realtime/token/).
2. Replace the mock implementation in `fetchLivekitToken()` with a call to your API, e.g.:

   ```ts
   const res = await fetch('/api/livekit-token', {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify({ displayName }),
   });
   const { token } = await res.json();
   return token;
   ```

3. Ensure your AI voice agent is orchestrated elsewhere (e.g. LiveKit Agents) and joins the same room.

## Authentication (Clerk)

[Clerk](https://clerk.com) is included as a dependency for future use. No login is required for the current dummy UI. When your backend is connected:

- Add `ClerkProvider` and wire `useAuth()` / `getToken()` for authenticated API calls.
- Use `getAuthHeaders(getToken)` from `src/api/clerk.ts` to attach the JWT to requests.

## Stack

- **Build:** Vite
- **Framework:** React + TypeScript
- **Styling:** Tailwind CSS
- **Auth:** Clerk
- **Voice:** LiveKit (WebRTC)

## Project structure

- `src/components/` — Window, ScreeningRoom
- `src/pages/` — OnboardingScreen, DatesGrid, ProfileScreen, ChatScreen
- `src/hooks/` — useLivekitRoom
- `src/api/` — clerk (auth headers), livekitClient, livekitToken
- `src/types/` — shared types
