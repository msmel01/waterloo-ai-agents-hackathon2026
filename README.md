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

## Deployment (Vercel)

- Vercel auto-detects Vite.
- **Build command:** `npm run build`
- **Output directory:** `dist/`
- Add `VITE_LIVEKIT_URL` in your Vercel project environment variables.

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

## Stack

- **Build:** Vite
- **Framework:** React + TypeScript
- **Styling:** Tailwind CSS
- **Voice:** LiveKit (WebRTC)

## Project structure

- `src/components/` — ConnectScreen, ScreeningRoom
- `src/hooks/` — useLivekitRoom
- `src/lib/` — livekitClient, livekitToken
- `src/types/` — shared types
