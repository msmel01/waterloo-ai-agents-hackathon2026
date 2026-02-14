import { Link, useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '@clerk/clerk-react';

import { useGetPublicProfileApiV1PublicSlugGet } from '../api/generated/public/public';
import { usePreCheckApiV1SessionsPreCheckGet } from '../api/generated/sessions/sessions';
import { Window } from '../components/Window';
import { AppHeader } from '../components/AppHeader';

export function ProfileScreen() {
  const { slug = '' } = useParams<{ slug: string }>();
  const navigate = useNavigate();
  const { isSignedIn } = useAuth();

  const profileQuery = useGetPublicProfileApiV1PublicSlugGet(slug, {
    query: { enabled: !!slug },
  });

  const preCheckQuery = usePreCheckApiV1SessionsPreCheckGet({
    query: { enabled: !!isSignedIn },
  });

  const handleBookChat = () => {
    if (!isSignedIn) {
      navigate('/sign-in');
      return;
    }
    navigate(`/chat/${slug}`);
  };

  if (profileQuery.isLoading) {
    return (
      <div className="min-h-screen bg-win-bg flex items-center justify-center">
        <p className="text-win-text text-sm">Loading profile…</p>
      </div>
    );
  }

  if (profileQuery.isError || !profileQuery.data) {
    return (
      <div className="min-h-screen bg-win-bg flex items-center justify-center px-4">
        <div className="max-w-md text-center">
          <p className="text-win-text text-sm mb-4">Profile not found for this link.</p>
          <Link
            to="/chats"
            className="inline-block px-4 py-2 bg-win-titlebar text-white text-sm border border-palette-orchid shadow-bevel"
          >
            Back to chats
          </Link>
        </div>
      </div>
    );
  }

  const heart = profileQuery.data;
  const canStart = isSignedIn
    ? Boolean(heart.is_accepting && (preCheckQuery.data?.can_start || preCheckQuery.data?.active_session_id))
    : Boolean(heart.is_accepting);

  return (
    <div className="min-h-screen bg-win-bg flex flex-col py-6 px-4">
      <AppHeader />

      <main className="flex-1 max-w-xl mx-auto w-full">
        <Link
          to="/chats"
          className="inline-block text-win-textMuted text-sm hover:text-win-text mb-4"
        >
          ← Back to chats
        </Link>
        <Window title={`${heart.display_name}Profile.exe`} icon="person">
          <div className="flex flex-col items-center">
            <div className="w-24 h-24 border border-gray-400 flex items-center justify-center mb-4 bg-gray-200 overflow-hidden">
              {heart.photo_url ? (
                <img src={heart.photo_url} alt={heart.display_name} className="w-full h-full object-cover" />
              ) : (
                <span className="text-win-titlebar text-3xl font-bold">{heart.display_name[0]}</span>
              )}
            </div>
            <h2 className="text-gray-800 text-xl font-semibold mb-2">{heart.display_name}</h2>
            <p className="text-gray-600 text-sm text-center mb-3">{heart.bio || 'No bio available yet.'}</p>
            <p className="text-gray-600 text-xs text-center mb-1">
              {heart.question_count} questions • {heart.estimated_duration}
            </p>
            {heart.persona_preview && (
              <p className="text-gray-600 text-xs text-center mb-4">Persona: {heart.persona_preview}</p>
            )}
            {isSignedIn && preCheckQuery.data && !preCheckQuery.data.can_start && !preCheckQuery.data.active_session_id && (
              <p className="text-red-600 text-xs text-center mb-4">{preCheckQuery.data.reason}</p>
            )}
            <button
              onClick={handleBookChat}
              disabled={!canStart}
              className="w-full py-2.5 bg-win-titlebar text-white text-sm font-medium border border-palette-orchid shadow-bevel hover:bg-win-titlebarLight transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {isSignedIn && preCheckQuery.data?.active_session_id ? 'Resume interview' : 'Start interview'}
            </button>
          </div>
        </Window>
      </main>
    </div>
  );
}
