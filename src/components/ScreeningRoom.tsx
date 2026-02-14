import { useState } from 'react';
import { useLivekitRoom } from '../hooks/useLivekitRoom';
import { getLivekitServerUrl } from '../lib/livekitClient';
import type { AuthState } from '../types';

interface ScreeningRoomProps {
  auth: AuthState;
  onLeave: () => void;
}

const isPlaceholderToken = (token: string) => token.startsWith('placeholder_');
const isPlaceholderUrl = (url: string) => url.includes('placeholder');

export function ScreeningRoom({ auth, onLeave }: ScreeningRoomProps) {
  const serverUrl = getLivekitServerUrl();
  const { token, displayName } = auth;
  const useDummyRoom = isPlaceholderToken(token) || isPlaceholderUrl(serverUrl);

  return (
    <div className="min-h-screen bg-stone-950 flex flex-col">
      <header className="flex items-center justify-center px-4 py-4 border-b border-stone-800">
        <h1 className="text-xl font-semibold text-rose-400">Valentine Hotline</h1>
      </header>

      {useDummyRoom ? (
        <DummyRoomContent displayName={displayName} onLeave={onLeave} />
      ) : (
        <LiveKitRoomWrapper
        token={token}
        serverUrl={serverUrl}
        displayName={displayName}
        onLeave={onLeave}
      />
      )}
    </div>
  );
}

/** TODO: Replace with real LiveKit connection when backend APIs are ready. */
function DummyRoomContent({
  displayName,
  onLeave,
}: {
  displayName: string;
  onLeave: () => void;
}) {
  const [isMuted, setIsMuted] = useState(false);

  return (
    <div className="flex-1 flex flex-col p-4 md:p-6">
      <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6 max-w-4xl mx-auto w-full">
        <div className="bg-stone-900/80 border border-stone-700/50 rounded-xl p-6 flex flex-col items-center">
          <h2 className="text-sm font-medium text-stone-400 mb-2">Suitor</h2>
          <p className="text-lg text-stone-100 font-medium mb-4">{displayName || 'You'}</p>
          <div className="h-12 w-24 rounded-full bg-stone-700/50 flex items-center justify-center mb-4">
            <div className="h-2 w-2 rounded-full bg-rose-500 animate-pulse" />
          </div>
          <p className="text-xs text-stone-500">Demo mode — awaiting backend</p>
        </div>
        <div className="bg-stone-900/80 border border-stone-700/50 rounded-xl p-6 flex flex-col items-center">
          <h2 className="text-sm font-medium text-stone-400 mb-2">Cindy&apos;s Gatekeeper</h2>
          <p className="text-lg text-stone-100 font-medium mb-4">Valentine Hotline AI</p>
          <div className="h-12 w-24 rounded-full bg-stone-700/50 flex items-center justify-center mb-4">
            <div className="h-2 w-2 rounded-full bg-stone-500" />
          </div>
          <p className="text-xs text-stone-500">Waiting for AI…</p>
        </div>
      </div>
      <div className="flex justify-center gap-4 py-6">
        <button
          onClick={() => setIsMuted((m) => !m)}
          className="px-6 py-3 rounded-lg bg-stone-800 hover:bg-stone-700 border border-stone-600 text-stone-200 font-medium transition-colors"
        >
          {isMuted ? 'Unmute' : 'Mute'}
        </button>
        <button
          onClick={onLeave}
          className="px-6 py-3 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-medium transition-colors"
        >
          Leave Hotline
        </button>
      </div>
    </div>
  );
}

function LiveKitRoomWrapper({
  token,
  serverUrl,
  displayName,
  onLeave,
}: {
  token: string;
  serverUrl: string;
  displayName: string;
  onLeave: () => void;
}) {
  const {
    isConnected,
    localParticipant,
    remoteParticipants,
    muteMic,
    unmuteMic,
    disconnect,
    isMuted,
  } = useLivekitRoom({ token, serverUrl });

  const handleLeave = () => {
    disconnect();
    onLeave();
  };

  const remoteArray = Array.from(remoteParticipants.values());

  return (
    <div className="flex-1 flex flex-col p-4 md:p-6">
      <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6 max-w-4xl mx-auto w-full">
        {/* Suitor panel */}
        <div className="bg-stone-900/80 border border-stone-700/50 rounded-xl p-6 flex flex-col items-center">
          <h2 className="text-sm font-medium text-stone-400 mb-2">Suitor</h2>
          <p className="text-lg text-stone-100 font-medium mb-4">
            {displayName || localParticipant?.name || 'You'}
          </p>
          <div className="h-12 w-24 rounded-full bg-stone-700/50 flex items-center justify-center mb-4">
            <div className="h-2 w-2 rounded-full bg-rose-500 animate-pulse" />
          </div>
          <p className="text-xs text-stone-500">
            {isConnected ? 'Connected' : 'Connecting…'}
          </p>
        </div>

        {/* AI Agent panel */}
        <div className="bg-stone-900/80 border border-stone-700/50 rounded-xl p-6 flex flex-col items-center">
          <h2 className="text-sm font-medium text-stone-400 mb-2">
            Cindy&apos;s Gatekeeper
          </h2>
          <p className="text-lg text-stone-100 font-medium mb-4">
            Valentine Hotline AI
          </p>
          <div className="h-12 w-24 rounded-full bg-stone-700/50 flex items-center justify-center mb-4 overflow-hidden">
            {remoteArray.length > 0 ? (
              <div className="flex gap-1 items-end h-6">
                {[1, 2, 3, 4, 5].map((i) => (
                  <div
                    key={i}
                    className="w-1.5 bg-rose-500 rounded-full animate-pulse"
                    style={{
                      height: `${6 + i * 3}px`,
                      animationDelay: `${i * 80}ms`,
                    }}
                  />
                ))}
              </div>
            ) : (
              <div className="h-2 w-2 rounded-full bg-stone-500" />
            )}
          </div>
          <p className="text-xs text-stone-500">
            {remoteArray.length > 0 ? 'AI is speaking…' : 'Waiting for AI…'}
          </p>
        </div>
      </div>

      {/* Bottom controls */}
      <div className="flex justify-center gap-4 py-6">
        <button
          onClick={isMuted ? unmuteMic : muteMic}
          className="px-6 py-3 rounded-lg bg-stone-800 hover:bg-stone-700 border border-stone-600 text-stone-200 font-medium transition-colors"
        >
          {isMuted ? 'Unmute' : 'Mute'}
        </button>
        <button
          onClick={handleLeave}
          className="px-6 py-3 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-medium transition-colors"
        >
          Leave Hotline
        </button>
      </div>
    </div>
  );
}
