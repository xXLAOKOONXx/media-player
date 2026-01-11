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

// Map event names to REST endpoints
const getRestEndpoint = (eventName: string): string => {
  return eventName === 'audio_status' 
    ? '/api/audio/playback/status'
    : '/api/video/playback/status';
};

/**
 * Custom hook to manage WebSocket connection for playback status updates
 * with automatic fallback to REST polling if WebSocket connection fails
 */
export function useWebSocketStatus({ eventName, onStatusUpdate, enabled = true }: UseWebSocketStatusOptions) {
  const [isConnected, setIsConnected] = useState(false);
  const [usePolling, setUsePolling] = useState(false);
  const socketRef = useRef<Socket | null>(null);
  const onStatusUpdateRef = useRef(onStatusUpdate);
  const pollingIntervalRef = useRef<number | null>(null);
  const connectionAttemptsRef = useRef(0);

  // Keep the callback ref up to date
  useEffect(() => {
    onStatusUpdateRef.current = onStatusUpdate;
  }, [onStatusUpdate]);

  // Polling fallback effect
  useEffect(() => {
    if (!enabled || !usePolling) {
      return;
    }

    console.log(`Using REST polling fallback for ${eventName}`);
    const endpoint = getRestEndpoint(eventName);

    const pollStatus = async () => {
      try {
        const response = await fetch(endpoint);
        if (response.ok) {
          const status = await response.json();
          onStatusUpdateRef.current(status);
        } else {
          console.error(`Failed to poll ${endpoint}: ${response.status}`);
        }
      } catch (error) {
        console.error(`Error polling ${endpoint}:`, error);
      }
    };

    // Poll immediately
    pollStatus();

    // Then poll every second
    pollingIntervalRef.current = window.setInterval(pollStatus, 1000);

    return () => {
      if (pollingIntervalRef.current !== null) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    };
  }, [eventName, enabled, usePolling]);

  // WebSocket connection effect
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
      setUsePolling(false);
      connectionAttemptsRef.current = 0;
    };

    const onDisconnect = (reason: string) => {
      console.log(`WebSocket disconnected for ${eventName}:`, reason);
      setIsConnected(false);
    };

    const onConnectError = (error: Error) => {
      console.error(`WebSocket connection error for ${eventName}:`, error);
      setIsConnected(false);
      connectionAttemptsRef.current++;

      // If we've failed multiple connection attempts, switch to polling
      if (connectionAttemptsRef.current >= 3) {
        console.warn(`WebSocket connection failed after ${connectionAttemptsRef.current} attempts, switching to REST polling`);
        setUsePolling(true);
        
        // Disconnect the socket to stop further reconnection attempts
        if (socketRef.current) {
          socketRef.current.disconnect();
        }
      }
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

  return { isConnected, usePolling };
}
