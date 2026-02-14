import { useCallback, useEffect, useState } from 'react';
import { useLiveKitRoom } from '@livekit/components-react';
import type { LocalParticipant, RemoteParticipant, Room } from 'livekit-client';
import { ConnectionState, RoomEvent } from 'livekit-client';

export interface UseLivekitRoomOptions {
  token: string;
  serverUrl: string;
}

export interface UseLivekitRoomReturn {
  isConnected: boolean;
  localParticipant: LocalParticipant | undefined;
  remoteParticipants: Map<string, RemoteParticipant>;
  room: Room | undefined;
  muteMic: () => void;
  unmuteMic: () => void;
  disconnect: () => void;
  isMuted: boolean;
}

export function useLivekitRoom({
  token,
  serverUrl,
}: UseLivekitRoomOptions): UseLivekitRoomReturn {
  const [isMuted, setIsMuted] = useState(false);
  const [connectionState, setConnectionState] = useState<ConnectionState>(ConnectionState.Disconnected);

  const { room } = useLiveKitRoom({
    serverUrl,
    token,
    connect: !!(token && serverUrl),
    audio: true,
    video: false,
    onConnected: () => setConnectionState(ConnectionState.Connected),
    onDisconnected: () => setConnectionState(ConnectionState.Disconnected),
    onError: (err) => {
      // eslint-disable-next-line no-console
      console.error('[LiveKit] Connection error:', err);
      setConnectionState(ConnectionState.Disconnected);
    },
  });

  useEffect(() => {
    if (!room) return;
    setConnectionState(room.state);
    const onConnected = () => setConnectionState(ConnectionState.Connected);
    const onDisconnected = () => setConnectionState(ConnectionState.Disconnected);
    room.on(RoomEvent.Connected, onConnected);
    room.on(RoomEvent.Disconnected, onDisconnected);
    return () => {
      room.off(RoomEvent.Connected, onConnected);
      room.off(RoomEvent.Disconnected, onDisconnected);
    };
  }, [room]);

  const muteMic = useCallback(() => {
    room?.localParticipant.setMicrophoneEnabled(false);
    setIsMuted(true);
  }, [room]);

  const unmuteMic = useCallback(() => {
    room?.localParticipant.setMicrophoneEnabled(true);
    setIsMuted(false);
  }, [room]);

  const disconnect = useCallback(() => {
    room?.disconnect(true);
  }, [room]);

  return {
    isConnected: connectionState === ConnectionState.Connected,
    localParticipant: room?.localParticipant,
    remoteParticipants: room?.remoteParticipants ?? new Map(),
    room,
    muteMic,
    unmuteMic,
    disconnect,
    isMuted,
  };
}
