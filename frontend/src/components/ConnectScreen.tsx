import { useState, FormEvent } from 'react';

interface ConnectScreenProps {
  onJoin: (displayName: string) => void;
  isJoining?: boolean;
}

export function ConnectScreen({ onJoin, isJoining = false }: ConnectScreenProps) {
  const [displayName, setDisplayName] = useState('');

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = displayName.trim();
    if (trimmed) onJoin(trimmed);
  };

  return (
    <div className="min-h-screen bg-y2k flex items-center justify-center p-4 relative">
      {/* Decorative sparkles */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <span className="absolute top-20 left-[15%] text-y2k-hotpink/40 text-2xl">✦</span>
        <span className="absolute top-32 right-[20%] text-y2k-cyan/50 text-xl">⋆</span>
        <span className="absolute bottom-40 left-[25%] text-y2k-lime/30 text-3xl">✧</span>
        <span className="absolute bottom-32 right-[15%] text-y2k-hotpink/40 text-xl">✦</span>
      </div>

      <div className="w-full max-w-md relative z-10">
        <div
          className="border-4 border-y2k-hotpink bg-black/60 p-8 relative"
          style={{ boxShadow: '0 0 20px rgba(255,20,147,0.4), inset 0 0 40px rgba(255,20,147,0.05)' }}
        >
          {/* MySpace-style corner bling */}
          <div className="absolute -top-1 -left-1 w-4 h-4 border-l-4 border-t-4 border-y2k-cyan" />
          <div className="absolute -top-1 -right-1 w-4 h-4 border-r-4 border-t-4 border-y2k-cyan" />
          <div className="absolute -bottom-1 -left-1 w-4 h-4 border-l-4 border-b-4 border-y2k-cyan" />
          <div className="absolute -bottom-1 -right-1 w-4 h-4 border-r-4 border-b-4 border-y2k-cyan" />

          <h1 className="font-rochester text-5xl text-y2k-hotpink text-glow-pink mb-2 text-center">
            Valentine Hotline
          </h1>
          <p className="font-pixel text-lg text-y2k-cyan/90 mb-6 text-center tracking-wider">
            Talk to our AI screener and see if you pass Cindy&apos;s coffee-date test.
          </p>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label
                htmlFor="displayName"
                className="block text-sm font-semibold text-y2k-cyan/90 mb-2 uppercase tracking-wider"
              >
                Your name
              </label>
              <input
                id="displayName"
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="Enter your name"
                className="w-full px-4 py-3 border-4 border-y2k-hotpink bg-black/80 text-y2k-cyan placeholder-stone-500 focus:outline-none focus:border-y2k-cyan font-pixel text-xl"
                style={{ boxShadow: 'inset 0 0 10px rgba(255,20,147,0.2)' }}
                disabled={isJoining}
                autoFocus
              />
            </div>
            <button
              type="submit"
              disabled={!displayName.trim() || isJoining}
              className="w-full py-4 px-4 border-4 border-y2k-lime bg-y2k-hotpink disabled:bg-stone-800 disabled:border-stone-600 disabled:text-stone-500 disabled:cursor-not-allowed text-black font-pixel text-xl uppercase tracking-wider hover:shadow-neon-lime hover:bg-y2k-magenta transition-all"
            >
              {isJoining ? 'Connecting…' : '♥ Join Valentine Hotline ♥'}
            </button>
          </form>
        </div>

        <p className="font-pixel text-y2k-cyan/60 text-center mt-4 text-sm">
          xoxo est. 2026
        </p>
      </div>
    </div>
  );
}
