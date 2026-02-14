/**
 * Fetches a LiveKit access token for the given display name.
 *
 * TODO: Replace this stub with a real backend call when APIs are ready.
 * Use getAuthHeaders(getToken) from src/api/clerk.ts to attach the JWT for backend verification.
 */
export async function fetchLivekitToken(displayName: string): Promise<string> {
  await new Promise((resolve) => setTimeout(resolve, 300)); // Simulate network delay
  return `placeholder_token_${displayName}_${Date.now()}`;
}
