import { useEffect, useState, useRef } from 'react';
import { io, Socket } from 'socket.io-client';

// Use relative URL - works for both dev (proxied) and production (same origin)
const getSocketUrl = () => {
  // In development with Vite proxy, use the dev server's origin
  // In production, use the current origin
  if (import.meta.env.DEV) {
    return 'http://localhost:5000';
  }
  return window.location.origin;
};

// Type definitions for playback status
export interface PlaybackStatus {
  is_playing: boolean;
  is_paused: boolean;
  volume: number;
  playlist_length: number;
  current_track_index: number | null;
  current_track: {
    title: string;
    path: string;
    duration: string | number;
    start_time?: number | null;
    end_time?: number | null;
    artist?: string;
    album?: string;
  } | null;
  next_track: {
    title: string;
    artist?: string;
    album?: string;
  } | null;
  shuffle: boolean;
  repeat_mode: 'none' | 'all' | 'one';
  current_position: number | null;
}

export interface VideoPlaybackStatus extends PlaybackStatus {
  audio_tracks: Array<{ id: number; label: string; selected: boolean }>;
  subtitle_tracks: Array<{ id: number; label: string; selected: boolean }>;
  current_audio_track_id: number | null;
  current_subtitle_track_id: number | null;
}

interface UseWebSocketStatusOptions {
  eventName: 'audio_status' | 'video_status';
  onStatusUpdate: (status: PlaybackStatus | VideoPlaybackStatus) => void;
  enabled?: boolean;
}

/**
 * Custom hook to manage WebSocket connection for playback status updates
 */
export function useWebSocketStatus({ eventName, onStatusUpdate, enabled = true }: UseWebSocketStatusOptions) {
  const [isConnected, setIsConnected] = useState(false);
  const socketRef = useRef<Socket | null>(null);
  const onStatusUpdateRef = useRef(onStatusUpdate);

  // Keep the callback ref up to date
  useEffect(() => {
    onStatusUpdateRef.current = onStatusUpdate;
  }, [onStatusUpdate]);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    // Create socket connection
    const socket = io(getSocketUrl(), {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionAttempts: 10,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      timeout: 20000,
    });

    socketRef.current = socket;

    // Connection event handlers
    const onConnect = () => {
      console.log(`WebSocket connected for ${eventName}`);
      setIsConnected(true);
    };

    const onDisconnect = (reason: string) => {
      console.log(`WebSocket disconnected for ${eventName}:`, reason);
      setIsConnected(false);
    };

    const onConnectError = (error: Error) => {
      console.error(`WebSocket connection error for ${eventName}:`, error);
      setIsConnected(false);
    };

    const onStatus = (status: PlaybackStatus | VideoPlaybackStatus) => {
      onStatusUpdateRef.current(status);
    };

    // Register event listeners
    socket.on('connect', onConnect);
    socket.on('disconnect', onDisconnect);
    socket.on('connect_error', onConnectError);
    socket.on(eventName, onStatus);

    // Cleanup on unmount
    return () => {
      socket.off('connect', onConnect);
      socket.off('disconnect', onDisconnect);
      socket.off('connect_error', onConnectError);
      socket.off(eventName, onStatus);
      socket.disconnect();
      socketRef.current = null;
    };
  }, [eventName, enabled]);

  return { isConnected };
}
