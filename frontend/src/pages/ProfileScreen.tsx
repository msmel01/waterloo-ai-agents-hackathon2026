import { Link, useNavigate, useParams } from 'react-router-dom';
import { Window } from '../components/Window';
import { AppHeader } from '../components/AppHeader';
import { PLACEHOLDER_DATES } from '../data/placeholders';

export function ProfileScreen() {
  const { slug } = useParams<{ slug: string }>();
  const navigate = useNavigate();

  const profile = PLACEHOLDER_DATES.find((d) => d.slug === slug);
  const displayName = profile?.name ?? slug ?? 'Unknown';

  const handleBookChat = () => {
    navigate(`/chat/${slug}`);
  };

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
        <Window title={`${displayName}Profile.exe`} icon="person">
          {/* TODO: Profile UI - placeholder for now */}
          <div className="flex flex-col items-center">
            <div className="w-24 h-24 border border-gray-400 flex items-center justify-center mb-4 bg-gray-200">
              <span className="text-win-titlebar text-3xl font-bold">{displayName[0]}</span>
            </div>
            <h2 className="text-gray-800 text-xl font-semibold mb-2">{displayName}</h2>
            <p className="text-gray-600 text-sm text-center mb-6">
              Profile details coming soon…
            </p>
            <button
              onClick={handleBookChat}
              className="w-full py-2.5 bg-win-titlebar text-white text-sm font-medium border border-palette-orchid shadow-bevel hover:bg-win-titlebarLight transition-colors"
            >
              Book a chat
            </button>
          </div>
        </Window>
      </main>
    </div>
  );
}
