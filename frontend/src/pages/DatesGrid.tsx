import { Link } from 'react-router-dom';
import { useAuth } from '@clerk/clerk-react';

import { useGetPublicProfileApiV1PublicSlugGet } from '../api/generated/public/public';
import { useGetMySessionsApiV1SuitorsMeSessionsGet } from '../api/generated/suitors/suitors';
import { Window } from '../components/Window';
import { AppHeader } from '../components/AppHeader';

const HEART_SLUG = import.meta.env.VITE_HEART_SLUG || 'heart';

export function DatesGrid() {
  const { isSignedIn } = useAuth();
  const heartQuery = useGetPublicProfileApiV1PublicSlugGet(HEART_SLUG);
  const sessionsQuery = useGetMySessionsApiV1SuitorsMeSessionsGet({
    query: { enabled: !!isSignedIn, refetchInterval: 30_000 },
  });

  return (
    <div className="min-h-screen bg-win-bg flex flex-col py-6 px-4">
      <AppHeader />

      <main className="flex-1 max-w-5xl mx-auto w-full space-y-4">
        <h2 className="text-win-text text-lg font-semibold">Your Valentine Hotline</h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
          {heartQuery.data ? (
            <Link to={`/profile/${HEART_SLUG}`} className="block">
              <Window title={`${heartQuery.data.display_name}.exe`} icon="person">
                <div className="flex flex-col items-center">
                  <div className="aspect-square w-20 h-20 border border-gray-400 flex items-center justify-center bg-gray-200 mb-3 overflow-hidden">
                    {heartQuery.data.photo_url ? (
                      <img
                        src={heartQuery.data.photo_url}
                        alt={heartQuery.data.display_name}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <span className="text-win-titlebar text-2xl font-bold">
                        {heartQuery.data.display_name[0]}
                      </span>
                    )}
                  </div>
                  <h3 className="text-gray-800 text-sm font-medium text-center">{heartQuery.data.display_name}</h3>
                  <p className="text-gray-600 text-xs text-center mt-1">
                    {heartQuery.data.question_count} questions • {heartQuery.data.estimated_duration}
                  </p>
                </div>
              </Window>
            </Link>
          ) : (
            <Window title="Hotline.exe" icon="info">
              <p className="text-gray-600 text-sm">
                {heartQuery.isLoading ? 'Loading hotline…' : 'No active hotline found.'}
              </p>
            </Window>
          )}
        </div>

        <Window title="SessionHistory.exe" icon="info">
          <div className="space-y-3">
            {isSignedIn ? (
              <p className="text-gray-700 text-sm">
                Daily limit: {sessionsQuery.data?.daily_limit ?? '-'} • Remaining today:{' '}
                {sessionsQuery.data?.remaining_today ?? '-'}
              </p>
            ) : (
              <p className="text-gray-700 text-sm">
                Sign in to view your session history and remaining attempts.
              </p>
            )}

            {isSignedIn && sessionsQuery.isLoading && <p className="text-gray-600 text-sm">Loading sessions…</p>}

            {isSignedIn && !sessionsQuery.isLoading && (sessionsQuery.data?.sessions.length ?? 0) === 0 && (
              <p className="text-gray-600 text-sm">No interview attempts yet.</p>
            )}

            <div className="space-y-2">
              {isSignedIn && sessionsQuery.data?.sessions.map((session) => (
                <div
                  key={session.session_id}
                  className="border border-gray-300 px-3 py-2 text-xs text-gray-700 bg-white"
                >
                  <p>
                    <span className="font-semibold">{session.status}</span>
                    {session.duration_seconds != null && ` • ${session.duration_seconds}s`}
                    {session.end_reason && ` • ${session.end_reason}`}
                  </p>
                  <p>
                    Verdict:{' '}
                    {session.has_verdict ? (session.verdict ?? 'ready') : 'pending'}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </Window>
      </main>
    </div>
  );
}
