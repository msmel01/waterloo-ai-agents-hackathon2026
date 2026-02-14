import { useState } from 'react';
import { Window } from './Window';
import { useLivekitRoom } from '../hooks/useLivekitRoom';
import { getLivekitServerUrl } from '../lib/livekitClient';
import type { AuthState } from '../types';

interface ScreeningRoomProps {
  auth: AuthState;
  onLeave: () => void;
  dateName?: string;
}

const isPlaceholderToken = (token: string) => token.startsWith('placeholder_');
const isPlaceholderUrl = (url: string) => url.includes('placeholder');

export function ScreeningRoom({ auth, onLeave, dateName = 'Date' }: ScreeningRoomProps) {
  const serverUrl = getLivekitServerUrl();
  const { token, displayName } = auth;
  const useDummyRoom = isPlaceholderToken(token) || isPlaceholderUrl(serverUrl);

  return (
    <div className="min-h-screen bg-win-bg flex flex-col">
      <header className="border-b border-win-border px-4 py-4">
        <h1 className="text-win-textMuted text-sm font-medium uppercase tracking-wider">
          Valentine Hotline
        </h1>
        <div className="h-px bg-win-border mt-1" />
      </header>

      {useDummyRoom ? (
        <DummyRoomContent displayName={displayName} onLeave={onLeave} dateName={dateName} />
      ) : (
        <LiveKitRoomWrapper
          token={token}
          serverUrl={serverUrl}
          displayName={displayName}
          onLeave={onLeave}
          dateName={dateName}
        />
      )}
    </div>
  );
}

/** TODO: Replace with real LiveKit connection when backend APIs are ready. */
function DummyRoomContent({
  displayName,
  onLeave,
  dateName,
}: {
  displayName: string;
  onLeave: () => void;
  dateName: string;
}) {
  const [isMuted, setIsMuted] = useState(false);

  return (
    <div className="flex-1 flex flex-col p-4 md:p-6">
      <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6 max-w-4xl mx-auto w-full">
        <Window title="Suitor.exe" icon="person">
          <div className="flex flex-col items-center">
            <p className="text-win-text text-sm mb-4">{displayName || 'You'}</p>
            <div className="h-14 w-28 border border-win-border bg-win-bg flex items-center justify-center mb-4">
              <div className="h-3 w-3 bg-win-titlebar" />
            </div>
            <p className="text-win-textMuted text-xs">Demo mode — awaiting backend</p>
          </div>
        </Window>
        <Window title={`${dateName}'s Gatekeeper.exe`} icon="person">
          <div className="flex flex-col items-center">
            <p className="text-win-text text-sm mb-4">Valentine Hotline AI</p>
            <div className="h-14 w-28 border border-win-border bg-win-bg flex items-center justify-center mb-4">
              <div className="h-3 w-3 bg-win-textMuted" />
            </div>
            <p className="text-win-textMuted text-xs">Waiting for AI…</p>
          </div>
        </Window>
      </div>
      <div className="flex justify-center gap-4 py-6">
        <button
          onClick={() => setIsMuted((m) => !m)}
          className="px-6 py-2.5 border border-win-border bg-win-content text-win-text text-sm hover:bg-win-titlebar hover:text-white hover:border-win-titlebar transition-colors"
        >
          {isMuted ? 'Unmute' : 'Mute'}
        </button>
        <button
          onClick={onLeave}
          className="px-6 py-2.5 bg-win-titlebar text-white text-sm font-medium hover:bg-win-titlebarLight transition-colors"
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
  dateName,
}: {
  token: string;
  serverUrl: string;
  displayName: string;
  onLeave: () => void;
  dateName: string;
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
        <Window title="Suitor.exe" icon="person">
          <div className="flex flex-col items-center">
            <p className="text-win-text text-sm mb-4">
              {displayName || localParticipant?.name || 'You'}
            </p>
            <div className="h-14 w-28 border border-win-border bg-win-bg flex items-center justify-center mb-4">
              <div className="h-3 w-3 bg-win-titlebar" />
            </div>
            <p className="text-win-textMuted text-xs">
              {isConnected ? 'Connected' : 'Connecting…'}
            </p>
          </div>
        </Window>

        <Window title={`${dateName}'s Gatekeeper.exe`} icon="person">
          <div className="flex flex-col items-center">
            <p className="text-win-text text-sm mb-4">Valentine Hotline AI</p>
            <div className="h-14 w-28 border border-win-border bg-win-bg flex items-center justify-center mb-4 overflow-hidden">
              {remoteArray.length > 0 ? (
                <div className="flex gap-1 items-end h-6">
                  {[1, 2, 3, 4, 5].map((i) => (
                    <div
                      key={i}
                      className="w-2 bg-win-titlebar animate-pulse"
                      style={{ height: `${6 + i * 3}px` }}
                    />
                  ))}
                </div>
              ) : (
                <div className="h-3 w-3 bg-win-textMuted" />
              )}
            </div>
            <p className="text-win-textMuted text-xs">
              {remoteArray.length > 0 ? 'AI is speaking…' : 'Waiting for AI…'}
            </p>
          </div>
        </Window>
      </div>

      <div className="flex justify-center gap-4 py-6">
        <button
          onClick={isMuted ? unmuteMic : muteMic}
          className="px-6 py-2.5 border border-win-border bg-win-content text-win-text text-sm hover:bg-win-titlebar hover:text-white hover:border-win-titlebar transition-colors"
        >
          {isMuted ? 'Unmute' : 'Mute'}
        </button>
        <button
          onClick={handleLeave}
          className="px-6 py-2.5 bg-win-titlebar text-white text-sm font-medium hover:bg-win-titlebarLight transition-colors"
        >
          Leave Hotline
        </button>
      </div>
    </div>
  );
}
