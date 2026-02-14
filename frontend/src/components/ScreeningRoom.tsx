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
    <div className="min-h-screen bg-y2k flex flex-col relative">
      {/* Decorative sparkles */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <span className="absolute top-24 left-[10%] text-y2k-hotpink/30 text-xl">✦</span>
        <span className="absolute top-40 right-[12%] text-y2k-cyan/40 text-2xl">⋆</span>
        <span className="absolute bottom-1/3 left-[8%] text-y2k-lime/25 text-xl">✧</span>
        <span className="absolute bottom-1/4 right-[10%] text-y2k-hotpink/30 text-2xl">✦</span>
      </div>

      <header
        className="flex items-center justify-center px-4 py-5 border-b-4 border-y2k-hotpink relative z-10"
        style={{ boxShadow: '0 4px 0 rgba(255,20,147,0.3)' }}
      >
        <h1 className="font-rochester text-4xl text-y2k-hotpink text-glow-pink">
          Valentine Hotline
        </h1>
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

function Panel({ children, cyan = false }: { children: React.ReactNode; cyan?: boolean }) {
  return (
    <div
      className={`border-4 bg-black/60 p-6 flex flex-col items-center relative ${cyan ? 'border-y2k-cyan' : 'border-y2k-hotpink'}`}
      style={{ boxShadow: '0 0 15px rgba(255,20,147,0.3), inset 0 0 30px rgba(255,20,147,0.05)' }}
    >
      <div className="absolute -top-1 -left-1 w-3 h-3 border-l-2 border-t-2 border-y2k-cyan" />
      <div className="absolute -top-1 -right-1 w-3 h-3 border-r-2 border-t-2 border-y2k-cyan" />
      <div className="absolute -bottom-1 -left-1 w-3 h-3 border-l-2 border-b-2 border-y2k-cyan" />
      <div className="absolute -bottom-1 -right-1 w-3 h-3 border-r-2 border-b-2 border-y2k-cyan" />
      {children}
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
    <div className="flex-1 flex flex-col p-4 md:p-6 relative z-10">
      <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-6 md:gap-8 max-w-4xl mx-auto w-full">
        <Panel>
          <h2 className="font-rochester text-3xl text-y2k-hotpink text-glow-pink mb-2">Suitor</h2>
          <p className="font-pixel text-xl text-y2k-cyan mb-4">{displayName || 'You'}</p>
          <div className="h-14 w-28 border-4 border-y2k-cyan/50 bg-black/50 flex items-center justify-center mb-4">
            <div className="h-3 w-3 bg-y2k-hotpink animate-pulse" style={{ boxShadow: '0 0 10px #ff1493' }} />
          </div>
          <p className="font-pixel text-sm text-y2k-cyan/70">Demo mode — awaiting backend</p>
        </Panel>
        <Panel cyan>
          <h2 className="font-rochester text-3xl text-y2k-cyan text-glow-cyan mb-2">Cindy&apos;s Gatekeeper</h2>
          <p className="font-rochester text-xl text-y2k-hotpink/90 mb-4">Valentine Hotline AI</p>
          <div className="h-14 w-28 border-4 border-y2k-hotpink/50 bg-black/50 flex items-center justify-center mb-4">
            <div className="h-3 w-3 bg-stone-500" />
          </div>
          <p className="font-pixel text-sm text-y2k-cyan/70">Waiting for AI…</p>
        </Panel>
      </div>
      <div className="flex justify-center gap-4 py-6">
        <button
          onClick={() => setIsMuted((m) => !m)}
          className="px-8 py-4 border-4 border-y2k-cyan bg-black/80 text-y2k-cyan font-pixel text-xl hover:shadow-neon-cyan hover:bg-y2k-cyan/20 transition-all"
        >
          {isMuted ? 'Unmute' : 'Mute'}
        </button>
        <button
          onClick={onLeave}
          className="px-8 py-4 border-4 border-y2k-lime bg-y2k-hotpink text-black font-pixel text-xl hover:shadow-neon-lime hover:bg-y2k-magenta transition-all"
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
    <div className="flex-1 flex flex-col p-4 md:p-6 relative z-10">
      <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-6 md:gap-8 max-w-4xl mx-auto w-full">
        <Panel>
          <h2 className="font-rochester text-3xl text-y2k-hotpink text-glow-pink mb-2">Suitor</h2>
          <p className="font-pixel text-xl text-y2k-cyan mb-4">
            {displayName || localParticipant?.name || 'You'}
          </p>
          <div className="h-14 w-28 border-4 border-y2k-cyan/50 bg-black/50 flex items-center justify-center mb-4">
            <div className="h-3 w-3 bg-y2k-hotpink animate-pulse" style={{ boxShadow: '0 0 10px #ff1493' }} />
          </div>
          <p className="font-pixel text-sm text-y2k-cyan/70">
            {isConnected ? 'Connected' : 'Connecting…'}
          </p>
        </Panel>

        <Panel cyan>
          <h2 className="font-rochester text-3xl text-y2k-cyan text-glow-cyan mb-2">
            Cindy&apos;s Gatekeeper
          </h2>
          <p className="font-rochester text-xl text-y2k-hotpink/90 mb-4">
            Valentine Hotline AI
          </p>
          <div className="h-14 w-28 border-4 border-y2k-hotpink/50 bg-black/50 flex items-center justify-center mb-4 overflow-hidden">
            {remoteArray.length > 0 ? (
              <div className="flex gap-1 items-end h-6">
                {[1, 2, 3, 4, 5].map((i) => (
                  <div
                    key={i}
                    className="w-2 bg-y2k-cyan animate-pulse"
                    style={{
                      height: `${6 + i * 3}px`,
                      animationDelay: `${i * 80}ms`,
                      boxShadow: '0 0 6px #00ffff',
                    }}
                  />
                ))}
              </div>
            ) : (
              <div className="h-3 w-3 bg-stone-500" />
            )}
          </div>
          <p className="font-pixel text-sm text-y2k-cyan/70">
            {remoteArray.length > 0 ? 'AI is speaking…' : 'Waiting for AI…'}
          </p>
        </Panel>
      </div>

      <div className="flex justify-center gap-4 py-6">
        <button
          onClick={isMuted ? unmuteMic : muteMic}
          className="px-8 py-4 border-4 border-y2k-cyan bg-black/80 text-y2k-cyan font-pixel text-xl hover:shadow-neon-cyan hover:bg-y2k-cyan/20 transition-all"
        >
          {isMuted ? 'Unmute' : 'Mute'}
        </button>
        <button
          onClick={handleLeave}
          className="px-8 py-4 border-4 border-y2k-lime bg-y2k-hotpink text-black font-pixel text-xl hover:shadow-neon-lime hover:bg-y2k-magenta transition-all"
        >
          Leave Hotline
        </button>
      </div>
    </div>
  );
}
