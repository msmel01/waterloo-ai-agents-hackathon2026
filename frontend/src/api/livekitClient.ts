/**
 * LiveKit connection helper.
 * Uses VITE_LIVEKIT_URL from environment (set in .env or Vercel project settings).
 */
export function getLivekitServerUrl(): string {
  const url = import.meta.env.VITE_LIVEKIT_URL;
  if (!url) {
    // Fallback for local dev; connection will fail until real URL is set
    return 'wss://placeholder.livekit.cloud';
  }
  return url;
}
