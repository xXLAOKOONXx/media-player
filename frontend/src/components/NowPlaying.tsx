import './NowPlaying.css';

const API_BASE_URL = '';

interface NowPlayingProps {
  status: any;
}

const NowPlaying = ({ status }: NowPlayingProps) => {
  if (!status || !status.current_track) {
    return (
      <div className="now-playing card">
        <h2>Now Playing</h2>
        <div className="empty-state">
          <p>🎵 No track playing</p>
          <p>Select a playlist from the Playlists tab to start playback</p>
        </div>
      </div>
    );
  }

  const { current_track, next_track, is_playing, is_paused, current_track_index, playlist_length, current_position } = status;

  const formatTime = (seconds: number | null | undefined) => {
    if (seconds == null) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleSeek = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const position = parseFloat(e.target.value);
    
    try {
      await fetch(`${API_BASE_URL}/api/playback/seek`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ position })
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
  const currentPos = current_position || 0;
  
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
          {is_playing && !is_paused && <span className="playing-icon">▶</span>}
          {is_paused && <span className="paused-icon">⏸</span>}
          <span className="title">{current_track.title}</span>
        </div>
        <div className="track-details">
          {current_track.artist && (
            <p className="track-artist">🎤 {current_track.artist}</p>
          )}
          {current_track.album && (
            <p className="track-album">💿 {current_track.album}</p>
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
                  value={currentPos}
                  onChange={handleSeek}
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
              <p className="next-track-title">🎵 {next_track.title}</p>
              {next_track.artist && (
                <p className="next-track-artist">🎤 {next_track.artist}</p>
              )}
              {next_track.album && (
                <p className="next-track-album">💿 {next_track.album}</p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default NowPlaying;