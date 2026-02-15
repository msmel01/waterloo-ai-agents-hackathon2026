import { RoomAudioRenderer } from '@livekit/components-react';
import { Window } from './Window';
import { AppHeader } from './AppHeader';
import { useLivekitRoom } from '../hooks/useLivekitRoom';
import type { SessionStatusResponse } from '../api/model';
import type { AuthState } from '../types';

interface ScreeningRoomProps {
  auth: AuthState;
  onLeave: () => void;
  dateName?: string;
  sessionStatus?: SessionStatusResponse;
}

export function ScreeningRoom({
  auth,
  onLeave,
  dateName = 'Date',
  sessionStatus,
}: ScreeningRoomProps) {
  const { token, displayName, livekitUrl: serverUrl } = auth;

  return (
    <div className="min-h-screen bg-win-bg flex flex-col">
      <div className="border-b border-win-border px-4 py-4">
        <AppHeader />
      </div>
      <LiveKitRoomWrapper
        token={token}
        serverUrl={serverUrl}
        displayName={displayName}
        onLeave={onLeave}
        dateName={dateName}
        sessionStatus={sessionStatus}
      />
    </div>
  );
}

function LiveKitRoomWrapper({
  token,
  serverUrl,
  displayName,
  onLeave,
  dateName,
  sessionStatus,
}: {
  token: string;
  serverUrl: string;
  displayName: string;
  onLeave: () => void;
  dateName: string;
  sessionStatus?: SessionStatusResponse;
}) {
  const {
    isConnected,
    localParticipant,
    remoteParticipants,
    room,
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
      {room ? <RoomAudioRenderer room={room} /> : null}
      <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6 max-w-4xl mx-auto w-full">
        <Window title="Suitor.exe" icon="person">
          <div className="flex flex-col items-center">
            <p className="text-gray-800 text-sm mb-4">
              {displayName || localParticipant?.name || 'You'}
            </p>
            <div className="h-14 w-28 border border-gray-400 bg-gray-200 flex items-center justify-center mb-4">
              <div className="h-3 w-3 bg-win-titlebar" />
            </div>
            <p className="text-gray-600 text-xs">
              {isConnected ? 'Connected' : 'Connecting…'}
            </p>
          </div>
        </Window>

        <Window title={`${dateName}'s Gatekeeper.exe`} icon="person">
          <div className="flex flex-col items-center">
            <p className="text-gray-800 text-sm mb-4">Valentine Hotline AI</p>
            <div className="h-14 w-28 border border-gray-400 bg-gray-200 flex items-center justify-center mb-4 overflow-hidden">
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
                <div className="h-3 w-3 bg-gray-500" />
              )}
            </div>
            <p className="text-gray-600 text-xs">
              {remoteArray.length > 0 ? 'AI is speaking…' : 'Waiting for AI…'}
            </p>
          </div>
        </Window>
      </div>

      {sessionStatus && (
        <div className="max-w-4xl mx-auto w-full mt-2 text-xs text-gray-600">
          <p>
            Status: {sessionStatus.status}
            {typeof sessionStatus.questions_asked === 'number' &&
              typeof sessionStatus.questions_total === 'number' &&
              ` • Questions: ${sessionStatus.questions_asked}/${sessionStatus.questions_total}`}
            {typeof sessionStatus.duration_seconds === 'number' &&
              ` • Duration: ${sessionStatus.duration_seconds}s`}
          </p>
        </div>
      )}

      <div className="flex justify-center gap-4 py-6">
        <button
          onClick={isMuted ? unmuteMic : muteMic}
          aria-pressed={isMuted}
          aria-label={isMuted ? 'Unmute microphone' : 'Mute microphone'}
          className="px-6 py-2.5 border border-palette-orchid shadow-bevel bg-palette-sand text-gray-800 text-sm hover:bg-win-titlebar hover:text-white hover:border-palette-orchid transition-colors"
        >
          {isMuted ? 'Unmute' : 'Mute'}
        </button>
        <button
          onClick={handleLeave}
          className="px-6 py-2.5 bg-win-titlebar text-white text-sm font-medium border border-palette-orchid shadow-bevel hover:bg-win-titlebarLight transition-colors"
        >
          Leave Hotline
        </button>
      </div>
    </div>
  );
}
