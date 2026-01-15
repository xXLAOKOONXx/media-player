import './VideoPlayer.css';
import { useEffect, useState } from 'react';

const API_BASE_URL = '';

interface VideoPlayerProps {
  status: any;
}

const VideoPlayer = ({ status }: VideoPlayerProps) => {
  const [isRatingModalOpen, setIsRatingModalOpen] = useState(false);
  const [ratingValue, setRatingValue] = useState(0);
  const [isSavingRating, setIsSavingRating] = useState(false);
  const [ratingError, setRatingError] = useState<string | null>(null);
  const [isSavingMusicPoint, setIsSavingMusicPoint] = useState<'start' | 'end' | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [dragPosition, setDragPosition] = useState<number>(0);

  useEffect(() => {
    if (!isRatingModalOpen) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setIsRatingModalOpen(false);
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [isRatingModalOpen]);

  if (!status || !status.current_track) {
    return (
      <div className="now-playing card">
        <h2>Now Playing</h2>
        <div className="empty-state">
          <p><span className="material-icons">music_note</span> No video playing</p>
          <p>Select a playlist from the Video Playlists tab to start playback</p>
        </div>
      </div>
    );
  }

  const { current_track, next_track, is_playing, is_paused, current_track_index, playlist_length, current_position } = status;

  const openRatingModal = () => {
    setRatingError(null);
    const existing = current_track?.user_rating;
    if (typeof existing === 'number' && Number.isFinite(existing)) {
      setRatingValue(Math.max(0, Math.min(10, Math.round(existing))));
    } else {
      setRatingValue(0);
    }
    setIsRatingModalOpen(true);
  };

  const saveRating = async () => {
    const mediaId = current_track?.media_id;
    if (!mediaId || typeof mediaId !== 'string') {
      setRatingError('Missing media_id for current video');
      return;
    }

    const normalized = Math.max(0, Math.min(10, ratingValue));
    setIsSavingRating(true);
    setRatingError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/video/metadata/user`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ media_id: mediaId, user_rating: normalized }),
      });

      if (response.status === 401) {
        setRatingError('Login required');
        return;
      }
      if (!response.ok) {
        const text = await response.text();
        setRatingError(text || 'Failed to save rating');
        return;
      }

      setIsRatingModalOpen(false);
    } catch (err) {
      console.error('Error saving rating:', err);
      setRatingError('Failed to save rating');
    } finally {
      setIsSavingRating(false);
    }
  };

  const formatTime = (seconds: number | null | undefined) => {
    if (seconds == null) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleSeekChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const position = parseFloat(e.target.value);
    setIsDragging(true);
    setDragPosition(position);
  };

  const handleSeekCommit = async () => {
    if (!isDragging) return;
    
    setIsDragging(false);
    
    try {
      await fetch(`${API_BASE_URL}/api/video/playback/seek`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ position: dragPosition })
      });
    } catch (err) {
      console.error('Error seeking:', err);
    }
  };

  // Parse duration to get total length
  const getDuration = () => {
    if (!current_track.duration || current_track.duration === 'Unknown') {
      return null;
    }
    return parseFloat(current_track.duration);
  };

  const duration = getDuration();
  const startTime = current_track.start_time || 0;
  const endTime = current_track.end_time || duration;
  const effectiveDuration = endTime ? endTime - startTime : duration;
  const currentPos = typeof current_position === 'number' && Number.isFinite(current_position) ? current_position : 0;

  const saveMusicPoint = async (which: 'start' | 'end') => {
    const mediaId = current_track?.media_id;
    if (!mediaId || typeof mediaId !== 'string') {
      console.error('Missing media_id for current video');
      return;
    }

    const ms = Math.max(0, Math.trunc(currentPos * 1000));
    setIsSavingMusicPoint(which);

    try {
      const response = await fetch(`${API_BASE_URL}/api/video/metadata/user`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          media_id: mediaId,
          ...(which === 'start' ? { start_time_in_ms: ms } : { end_time_in_ms: ms }),
        }),
      });

      if (!response.ok) {
        const text = await response.text().catch(() => '');
        console.error(`Failed to set music_${which}`, text || response.statusText);
      }
    } catch (err) {
      console.error(`Error setting music_${which}:`, err);
    } finally {
      setIsSavingMusicPoint(null);
    }
  };
  
  // Calculate progress percentage
  const progressPercent = effectiveDuration && currentPos ? 
    Math.min(100, Math.max(0, ((currentPos - startTime) / effectiveDuration) * 100)) : 0;

  // Calculate crossfade regions (5 seconds before end, 3 seconds fade)
  const fadeOutStart = endTime ? endTime - 5 : null;
  const fadeOutStartPercent = fadeOutStart && effectiveDuration ? 
    ((fadeOutStart - startTime) / effectiveDuration) * 100 : null;

  return (
    <div className="now-playing card">
      <h2>Now Playing</h2>
      <div className="track-info">
        <div className="track-title">
          {is_playing && !is_paused && <span className="material-icons playing-icon">play_arrow</span>}
          {is_paused && <span className="material-icons paused-icon">pause</span>}
          <span className="title">{current_track.title}</span>

          <div className="video-player-title-actions">
            <button
              type="button"
              className="video-player-like-btn video-player-time-btn"
              onClick={() => saveMusicPoint('start')}
              disabled={!current_track?.media_id || isSavingMusicPoint !== null}
              title={!current_track?.media_id ? 'Missing media_id' : 'Set music_start to current timestamp'}
              aria-label="Set music_start to current timestamp"
            >
              <span className="material-icons">timer</span>
              <span className="video-player-time-btn-label">Set music_start</span>
            </button>

            <button
              type="button"
              className="video-player-like-btn video-player-time-btn"
              onClick={() => saveMusicPoint('end')}
              disabled={!current_track?.media_id || isSavingMusicPoint !== null}
              title={!current_track?.media_id ? 'Missing media_id' : 'Set music_end to current timestamp'}
              aria-label="Set music_end to current timestamp"
            >
              <span className="material-icons">timer</span>
              <span className="video-player-time-btn-label">Set music_end</span>
            </button>

            <button
              type="button"
              className="video-player-like-btn"
              onClick={openRatingModal}
              disabled={!current_track?.media_id}
              title={!current_track?.media_id ? 'Missing media_id' : 'Rate this video'}
              aria-label="Rate this video"
            >
              <span className="material-icons">thumb_up</span>
            </button>
          </div>
        </div>
        <div className="track-details">
          {current_track.artist && (
            <p className="track-artist"><span className="material-icons">person</span> {current_track.artist}</p>
          )}
          {current_track.album && (
            <p className="track-album"><span className="material-icons">album</span> {current_track.album}</p>
          )}
          {(current_track.start_time != null || current_track.end_time != null) && (
            <p className="track-custom-times">
              Custom Range: {formatTime(current_track.start_time) || '0:00'} - {formatTime(current_track.end_time) || 'end'}
            </p>
          )}
        </div>
        
        {/* Progress bar with time display */}
        <div className="progress-section">
          <div className="time-display">
            <span className="current-time">{formatTime(currentPos)}</span>
            <span className="total-time">{effectiveDuration ? formatTime(startTime + effectiveDuration) : '--:--'}</span>
          </div>
          
          {effectiveDuration && (
            <div className="progress-bar-container">
              <div className="progress-bar-wrapper">
                {/* Crossfade fade-out region visualization */}
                {fadeOutStartPercent !== null && (
                  <div 
                    className="crossfade-region"
                    style={{
                      left: `${fadeOutStartPercent}%`,
                      width: `${100 - fadeOutStartPercent}%`
                    }}
                    title="Crossfade fade-out region"
                  />
                )}
                
                {/* Progress bar */}
                <div className="progress-bar-background">
                  <div 
                    className="progress-bar-fill"
                    style={{ width: `${progressPercent}%` }}
                  />
                </div>
                
                {/* Seekable input */}
                <input
                  type="range"
                  min={startTime}
                  max={endTime || duration || 100}
                  step="0.1"
                  value={isDragging ? dragPosition : currentPos}
                  onChange={handleSeekChange}
                  onMouseUp={handleSeekCommit}
                  onTouchEnd={handleSeekCommit}
                  className="progress-bar-input"
                  disabled={!is_playing}
                />
              </div>
            </div>
          )}
        </div>
        
        <div className="playlist-info">
          Track {current_track_index + 1} of {playlist_length}
        </div>

        {/* Up Next section */}
        {next_track && (
          <div className="up-next">
            <h3>Up Next</h3>
            <div className="next-track-info">
              <p className="next-track-title"><span className="material-icons">music_note</span> {next_track.title}</p>
              {next_track.artist && (
                <p className="next-track-artist"><span className="material-icons">person</span> {next_track.artist}</p>
              )}
              {next_track.album && (
                <p className="next-track-album"><span className="material-icons">album</span> {next_track.album}</p>
              )}
            </div>
          </div>
        )}
      </div>

      {isRatingModalOpen && (
        <div
          className="video-player-rating-overlay"
          role="dialog"
          aria-modal="true"
          onClick={() => setIsRatingModalOpen(false)}
        >
          <div className="video-player-rating-modal card" onClick={(e) => e.stopPropagation()}>
            <div className="video-player-rating-header">
              <h3>Rate video</h3>
              <button
                type="button"
                className="video-player-rating-close"
                onClick={() => setIsRatingModalOpen(false)}
                aria-label="Close"
              >
                <span className="material-icons">close</span>
              </button>
            </div>

            <div className="video-player-rating-body">
              <div className="video-player-rating-row">
                <input
                  type="range"
                  min={0}
                  max={10}
                  step={1}
                  value={ratingValue}
                  onChange={(e) => setRatingValue(Number(e.target.value))}
                  disabled={isSavingRating}
                />
                <div className="video-player-rating-value">{ratingValue}</div>
              </div>

              {ratingError && <div className="video-player-rating-error">{ratingError}</div>}

              <div className="video-player-rating-actions">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setIsRatingModalOpen(false)}
                  disabled={isSavingRating}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={saveRating}
                  disabled={isSavingRating}
                >
                  {isSavingRating ? 'Saving…' : 'Save'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default VideoPlayer;