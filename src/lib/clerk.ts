/**
 * Clerk auth helpers for backend API calls.
 *
 * When your backend is connected, use getAuthHeaders() to attach the Clerk
 * session token to requests. The backend can then verify the JWT and access
 * user data.
 *
 * Example usage (in your API client when backend exists):
 *
 *   import { useAuth } from '@clerk/clerk-react';
 *
 *   const { getToken } = useAuth();
 *
 *   const res = await fetch('/api/livekit-token', {
 *     method: 'POST',
 *     headers: {
 *       'Content-Type': 'application/json',
 *       ...(await getAuthHeaders(getToken)),
 *     },
 *     body: JSON.stringify({ displayName }),
 *   });
 *
 * Or with a helper:
 *
 *   const headers = await getAuthHeaders(getToken);
 *   const res = await fetch(url, { ...options, headers: { ...options.headers, ...headers } });
 */
export async function getAuthHeaders(
  getToken: () => Promise<string | null>
): Promise<Record<string, string>> {
  const token = await getToken()
  if (!token) return {}
  return { Authorization: `Bearer ${token}` }
}
