/**
 * Fetches a LiveKit access token for the given display name.
 *
 * TODO: Replace this mock with a real backend call.
 * In production, call your token-issuing API, e.g.:
 *   const res = await fetch('/api/livekit-token', {
 *     method: 'POST',
 *     body: JSON.stringify({ displayName }),
 *   });
 *   const { token } = await res.json();
 *   return token;
 */
export async function fetchLivekitToken(displayName: string): Promise<string> {
  // Mock implementation: return a placeholder token.
  // This will NOT connect to a real LiveKit room until you plug in
  // your backend that issues valid tokens via the LiveKit Access Token API.
  await new Promise((resolve) => setTimeout(resolve, 300)); // Simulate network delay

  // eslint-disable-next-line no-console
  console.warn(
    '[livekitToken] Using placeholder token. Replace fetchLivekitToken with real backend call.'
  );

  return `placeholder_token_${displayName}_${Date.now()}`;
}
