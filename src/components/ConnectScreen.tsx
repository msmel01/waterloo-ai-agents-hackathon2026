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
    <div className="min-h-screen bg-hearts flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="bg-stone-900/80 border border-stone-700/50 rounded-2xl shadow-xl shadow-rose-950/20 p-8">
          <h1 className="font-rochester text-4xl text-rose-400 mb-1">
            Valentine Hotline
          </h1>
          <p className="text-stone-400 text-sm mb-6">
            Talk to our AI screener and see if you pass Cindy&apos;s coffee-date test.
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label
                htmlFor="displayName"
                className="block text-sm font-medium text-stone-300 mb-2"
              >
                Your name
              </label>
              <input
                id="displayName"
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="Enter your name"
                className="w-full px-4 py-3 rounded-lg bg-stone-800 border border-stone-600 text-stone-100 placeholder-stone-500 focus:outline-none focus:ring-2 focus:ring-rose-500/50 focus:border-rose-500"
                disabled={isJoining}
                autoFocus
              />
            </div>
            <button
              type="submit"
              disabled={!displayName.trim() || isJoining}
              className="w-full py-3 px-4 rounded-lg bg-rose-600 hover:bg-rose-500 disabled:bg-stone-700 disabled:text-stone-500 disabled:cursor-not-allowed text-white font-medium transition-colors"
            >
              {isJoining ? 'Connecting…' : 'Join Valentine Hotline'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
