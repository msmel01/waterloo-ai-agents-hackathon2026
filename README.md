# Valentine Hotline

Client UI for a voice-based **Virtual Dating Assistant** — a WebRTC room where a **suitor** joins from the browser (mic access) and an **AI voice agent** (via LiveKit) is the other participant.

## Setup

```bash
npm install
npm run dev
```

## Build

```bash
npm run build
```

Output directory: `dist/`

## Environment

| Variable | Description |
|----------|-------------|
| `VITE_LIVEKIT_URL` | LiveKit server URL (e.g. `wss://your-project.livekit.cloud`). Set in `.env` for local dev and in Vercel project settings for production. |
| `VITE_CLERK_PUBLISHABLE_KEY` | Clerk publishable key (from [Clerk Dashboard](https://dashboard.clerk.com) → API Keys). Required for authentication. Add when connecting your backend. |

## Deployment (Vercel)

- Vercel auto-detects Vite.
- **Build command:** `npm run build`
- **Output directory:** `dist/`
- Add `VITE_LIVEKIT_URL` and `VITE_CLERK_PUBLISHABLE_KEY` in your Vercel project environment variables.

## Token fetching

The app currently uses a **placeholder token** in `src/lib/livekitToken.ts`. To connect to a real LiveKit room:

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

The app uses [Clerk](https://clerk.com) for authentication. Auth state and tokens are available via `useAuth()` from `@clerk/clerk-react`. When your backend is connected:

- Use `getToken()` from `useAuth()` to obtain the session JWT.
- Attach it to API requests via `getAuthHeaders(getToken)` from `src/lib/clerk.ts`.
- Your backend can verify the JWT and access user data.

No backend is included in this repo; connect your API separately and wire it into `fetchLivekitToken` and any other endpoints.

## Stack

- **Build:** Vite
- **Framework:** React + TypeScript
- **Styling:** Tailwind CSS
- **Auth:** Clerk
- **Voice:** LiveKit (WebRTC)

## Project structure

- `src/components/` — ConnectScreen, ScreeningRoom
- `src/hooks/` — useLivekitRoom
- `src/lib/` — clerk (auth headers), livekitClient, livekitToken
- `src/types/` — shared types
