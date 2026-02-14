import { Link, useNavigate, useParams } from 'react-router-dom';
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
    <div className="min-h-screen bg-y2k flex flex-col relative">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <span className="absolute top-24 left-[10%] text-y2k-hotpink/30 text-xl">✦</span>
        <span className="absolute bottom-1/3 right-[12%] text-y2k-cyan/40 text-2xl">⋆</span>
      </div>

      <header
        className="flex items-center justify-center px-4 py-5 border-b-4 border-y2k-hotpink relative z-10"
        style={{ boxShadow: '0 4px 0 rgba(255,20,147,0.3)' }}
      >
        <h1 className="font-rochester text-4xl text-y2k-hotpink text-glow-pink">
          Valentine Hotline
        </h1>
      </header>

      <main className="flex-1 p-6 relative z-10">
        <Link
          to="/dates"
          className="inline-block font-pixel text-y2k-cyan/80 hover:text-y2k-cyan mb-4"
        >
          ← Back to dates
        </Link>
        <div className="max-w-xl mx-auto">
          {/* TODO: Profile UI - placeholder for now */}
          <div
            className="border-4 border-y2k-cyan bg-black/60 p-8"
            style={{ boxShadow: '0 0 15px rgba(0,255,255,0.2)' }}
          >
            <div className="aspect-square max-w-[200px] mx-auto mb-6 bg-y2k-purple/20 border-2 border-y2k-hotpink/50 flex items-center justify-center">
              <span className="font-rochester text-6xl text-y2k-hotpink">{displayName[0]}</span>
            </div>
            <h2 className="font-rochester text-4xl text-y2k-cyan text-center mb-4">
              {displayName}
            </h2>
            <p className="font-pixel text-y2k-cyan/70 text-center mb-8">
              Profile details coming soon…
            </p>
            <button
              onClick={handleBookChat}
              className="w-full py-4 border-4 border-y2k-lime bg-y2k-hotpink text-black font-pixel text-xl uppercase tracking-wider hover:shadow-neon-lime hover:bg-y2k-magenta transition-all"
            >
              Book a chat
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
