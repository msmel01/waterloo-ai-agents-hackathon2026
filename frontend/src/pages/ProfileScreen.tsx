import { Link, useNavigate, useParams } from 'react-router-dom';
import { Window } from '../components/Window';
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
      <header className="w-full max-w-xl mx-auto mb-6">
        <h1 className="text-win-textMuted text-sm font-medium uppercase tracking-wider">
          Valentine Hotline
        </h1>
        <div className="h-px bg-win-border mt-1" />
      </header>

      <main className="flex-1 max-w-xl mx-auto w-full">
        <Link
          to="/dates"
          className="inline-block text-win-textMuted text-sm hover:text-win-text mb-4"
        >
          ← Back to dates
        </Link>
        <Window title={`${displayName}Profile.exe`} icon="person">
          {/* TODO: Profile UI - placeholder for now */}
          <div className="flex flex-col items-center">
            <div className="w-24 h-24 border border-win-border flex items-center justify-center mb-4 bg-win-bg">
              <span className="text-win-titlebar text-3xl font-bold">{displayName[0]}</span>
            </div>
            <h2 className="text-win-text text-xl font-semibold mb-2">{displayName}</h2>
            <p className="text-win-textMuted text-sm text-center mb-6">
              Profile details coming soon…
            </p>
            <button
              onClick={handleBookChat}
              className="w-full py-2.5 bg-win-titlebar text-white text-sm font-medium hover:bg-win-titlebarLight transition-colors"
            >
              Book a chat
            </button>
          </div>
        </Window>
      </main>
    </div>
  );
}
