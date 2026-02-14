import { useState, FormEvent } from 'react';
import { Window } from './Window';

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
    <div className="min-h-screen bg-win-bg flex flex-col items-center py-6 px-4">
      <header className="w-full max-w-md mb-6">
        <h1 className="text-win-textMuted text-sm font-medium uppercase tracking-wider">
          Valentine Hotline
        </h1>
        <div className="h-px bg-win-border mt-1" />
      </header>

      <div className="w-full max-w-md">
        <Window title="ValentineHotline.exe" icon="phone">
          <p className="text-win-textMuted text-sm mb-4">
            Talk to our AI screener and see if you pass Cindy&apos;s coffee-date test.
          </p>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="displayName" className="block text-win-textMuted text-sm mb-1">
                Your name
              </label>
              <input
                id="displayName"
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="Enter your name"
                className="w-full px-3 py-2 bg-win-bg border border-win-border text-white placeholder-win-textMuted text-sm focus:outline-none focus:border-win-titlebar"
                disabled={isJoining}
                autoFocus
              />
            </div>
            <button
              type="submit"
              disabled={!displayName.trim() || isJoining}
              className="w-full py-2.5 bg-win-titlebar text-white text-sm font-medium disabled:bg-win-border disabled:text-win-textMuted disabled:cursor-not-allowed hover:bg-win-titlebarLight transition-colors"
            >
              {isJoining ? 'Connecting…' : 'Join Valentine Hotline'}
            </button>
          </form>
        </Window>
      </div>
    </div>
  );
}
