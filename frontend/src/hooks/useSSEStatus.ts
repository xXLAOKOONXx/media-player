import { useEffect, useState, useRef, useCallback } from 'react';

// Type definitions for playback status
export interface PlaybackStatus {
  is_playing: boolean;
  is_paused: boolean;
  volume: number;
  playlist_length: number;
  current_track_index: number;
  current_track: {
    title: string;
    path: string;
    duration: string;
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
  repeat_mode: 'none' | 'one' | 'all';
  current_position: number;
}

export interface VideoPlaybackStatus extends PlaybackStatus {
  audio_tracks?: any[];
  subtitle_tracks?: any[];
  current_audio_track_id?: number;
  current_subtitle_track_id?: number;
}

interface UseSSEStatusOptions {
  endpoint: '/api/audio/playback/events' | '/api/video/playback/events';
  onStatusUpdate: (status: PlaybackStatus | VideoPlaybackStatus) => void;
  enabled?: boolean;
}

/**
 * Custom hook to manage Server-Sent Events (SSE) connection for playback status updates
 * with automatic reconnection on failure
 * 
 * SSE provides one-way server-to-client communication over HTTP, making it more reliable
 * than WebSockets for status updates. The browser's EventSource API handles reconnection
 * automatically.
 */
export function useSSEStatus({ endpoint, onStatusUpdate, enabled = true }: UseSSEStatusOptions) {
  const [isConnected, setIsConnected] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);
  const onStatusUpdateRef = useRef(onStatusUpdate);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const reconnectAttemptsRef = useRef(0);

  // Keep the callback ref up to date
  useEffect(() => {
    onStatusUpdateRef.current = onStatusUpdate;
  }, [onStatusUpdate]);

  const connect = useCallback(() => {
    if (!enabled) return;

    try {
      console.log(`Connecting to SSE endpoint: ${endpoint}`);
      const eventSource = new EventSource(endpoint);
      eventSourceRef.current = eventSource;

      eventSource.onopen = () => {
        console.log(`SSE connected: ${endpoint}`);
        setIsConnected(true);
        reconnectAttemptsRef.current = 0; // Reset on successful connection
      };

      eventSource.onmessage = (event) => {
        try {
          const status = JSON.parse(event.data);
          onStatusUpdateRef.current(status);
        } catch (err) {
          console.error('Failed to parse SSE message:', err);
        }
      };

      eventSource.onerror = (error) => {
        console.error(`SSE error: ${endpoint}`, error);
        setIsConnected(false);
        
        // Close the connection
        if (eventSourceRef.current) {
          eventSourceRef.current.close();
          eventSourceRef.current = null;
        }

        // Exponential backoff for reconnection (1s, 2s, 4s, 8s, max 30s)
        const maxReconnectDelay = 30000;
        const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), maxReconnectDelay);
        reconnectAttemptsRef.current++;
        
        console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current})...`);
        reconnectTimeoutRef.current = window.setTimeout(() => {
          connect();
        }, delay);
      };
    } catch (err) {
      console.error('Failed to create EventSource:', err);
      setIsConnected(false);
    }
  }, [endpoint, enabled]);

  useEffect(() => {
    if (!enabled) {
      // Cleanup if disabled
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
      setIsConnected(false);
      return;
    }

    connect();

    return () => {
      // Cleanup on unmount
      if (eventSourceRef.current) {
        console.log(`Disconnecting from SSE: ${endpoint}`);
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
      setIsConnected(false);
    };
  }, [endpoint, enabled, connect]);

  return { isConnected };
}
