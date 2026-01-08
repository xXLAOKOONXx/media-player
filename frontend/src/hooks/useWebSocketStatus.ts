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

interface UseWebSocketStatusOptions {
  eventName: 'audio_status' | 'video_status';
  onStatusUpdate: (status: any) => void;
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
    socket.on('connect', () => {
      console.log(`WebSocket connected for ${eventName}`);
      setIsConnected(true);
    });

    socket.on('disconnect', (reason) => {
      console.log(`WebSocket disconnected for ${eventName}:`, reason);
      setIsConnected(false);
    });

    socket.on('connect_error', (error) => {
      console.error(`WebSocket connection error for ${eventName}:`, error);
      setIsConnected(false);
    });

    // Listen for status updates
    socket.on(eventName, (status) => {
      onStatusUpdateRef.current(status);
    });

    // Cleanup on unmount
    return () => {
      socket.off(eventName);
      socket.disconnect();
      socketRef.current = null;
    };
  }, [eventName, enabled]);

  return { isConnected };
}
