import { useState, useEffect, useRef } from 'react';

interface PlaybackStatus {
  is_playing?: boolean;
  is_paused?: boolean;
  current_position?: number | null;
  [key: string]: any;
}

/**
 * Custom hook to interpolate the current playback position between WebSocket updates
 * 
 * Since WebSocket only broadcasts when state changes (play/pause/stop/volume/etc),
 * the position needs to be interpolated on the client side to show smooth progress
 * when a track is playing.
 */
export function useInterpolatedPosition(status: PlaybackStatus | null) {
  const [interpolatedStatus, setInterpolatedStatus] = useState<PlaybackStatus | null>(status);
  const lastUpdateTime = useRef<number>(Date.now());
  const lastPosition = useRef<number | null>(null);
  const animationFrameId = useRef<number | null>(null);

  // Update when status changes from WebSocket
  useEffect(() => {
    if (status) {
      lastUpdateTime.current = Date.now();
      lastPosition.current = status.current_position ?? null;
      setInterpolatedStatus(status);
    }
  }, [status]);

  // Interpolate position when playing
  useEffect(() => {
    const interpolate = () => {
      if (!status || !status.is_playing || status.is_paused) {
        // Not playing, no need to interpolate
        animationFrameId.current = null;
        return;
      }

      const now = Date.now();
      const elapsedSeconds = (now - lastUpdateTime.current) / 1000;
      const basePosition = lastPosition.current ?? 0;
      const currentPosition = basePosition + elapsedSeconds;

      setInterpolatedStatus(prev => ({
        ...prev!,
        current_position: currentPosition,
      }));

      animationFrameId.current = requestAnimationFrame(interpolate);
    };

    // Start interpolation if playing
    if (status?.is_playing && !status.is_paused) {
      animationFrameId.current = requestAnimationFrame(interpolate);
    } else {
      // Stop interpolation if not playing
      if (animationFrameId.current !== null) {
        cancelAnimationFrame(animationFrameId.current);
        animationFrameId.current = null;
      }
    }

    // Cleanup
    return () => {
      if (animationFrameId.current !== null) {
        cancelAnimationFrame(animationFrameId.current);
        animationFrameId.current = null;
      }
    };
  }, [status?.is_playing, status?.is_paused]);

  return interpolatedStatus;
}
