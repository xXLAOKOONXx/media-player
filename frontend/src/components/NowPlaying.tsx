import './NowPlaying.css';

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
          <p>Select a playlist from the Library tab to start playback</p>
        </div>
      </div>
    );
  }

  const { current_track, is_playing, is_paused, current_track_index, playlist_length } = status;
  const metadata = current_track.metadata;

  const formatTime = (seconds: number | null | undefined) => {
    if (seconds == null) return null;
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatDuration = (seconds: number | null | undefined) => {
    if (seconds == null) return null;
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="now-playing card">
      <h2>Now Playing</h2>
      <div className="track-info">
        <div className="track-title">
          {is_playing && !is_paused && <span className="playing-icon">▶</span>}
          {is_paused && <span className="paused-icon">⏸</span>}
          <span className="title">{metadata?.title || current_track.title}</span>
        </div>
        
        {/* Display metadata if available */}
        {metadata && (
          <div className="track-metadata">
            {metadata.artist && (
              <p className="metadata-field">
                <span className="metadata-label">Artist:</span>
                <span className="metadata-value">{metadata.artist}</span>
              </p>
            )}
            {metadata.album && (
              <p className="metadata-field">
                <span className="metadata-label">Album:</span>
                <span className="metadata-value">{metadata.album}</span>
              </p>
            )}
            {metadata.year && (
              <p className="metadata-field">
                <span className="metadata-label">Year:</span>
                <span className="metadata-value">{metadata.year}</span>
              </p>
            )}
            {metadata.track_number && (
              <p className="metadata-field">
                <span className="metadata-label">Track #:</span>
                <span className="metadata-value">{metadata.track_number}</span>
              </p>
            )}
            {metadata.duration && (
              <p className="metadata-field">
                <span className="metadata-label">Duration:</span>
                <span className="metadata-value">{formatDuration(metadata.duration)}</span>
              </p>
            )}
          </div>
        )}
        
        <div className="track-details">
          <p className="track-path">{current_track.path}</p>
          {(current_track.start_time != null || current_track.end_time != null) && (
            <p className="track-custom-times">
              Custom Range: {formatTime(current_track.start_time) || '0:00'} - {formatTime(current_track.end_time) || 'end'}
            </p>
          )}
        </div>
        
        {/* Display custom tags if available */}
        {metadata && metadata.custom_tags && Object.keys(metadata.custom_tags).length > 0 && (
          <div className="custom-tags">
            <h3>Custom Tags</h3>
            <div className="tags-list">
              {Object.entries(metadata.custom_tags).map(([key, value]) => (
                <div key={key} className="tag-item">
                  <span className="tag-key">{key}:</span>
                  <span className="tag-value">{value as string}</span>
                </div>
              ))}
            </div>
          </div>
        )}
        
        <div className="playlist-info">
          Track {current_track_index + 1} of {playlist_length}
        </div>
      </div>
    </div>
  );
};

export default NowPlaying;