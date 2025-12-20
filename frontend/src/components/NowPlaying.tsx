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

  const formatTime = (seconds: number | null | undefined) => {
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
          <span className="title">{current_track.title}</span>
        </div>
        <div className="track-details">
          <p className="track-path">{current_track.path}</p>
          {current_track.duration && current_track.duration !== 'Unknown' && (
            <p className="track-duration">Duration: {current_track.duration}s</p>
          )}
          {(current_track.start_time != null || current_track.end_time != null) && (
            <p className="track-custom-times">
              Custom Range: {formatTime(current_track.start_time) || '0:00'} - {formatTime(current_track.end_time) || 'end'}
            </p>
          )}
        </div>
        <div className="playlist-info">
          Track {current_track_index + 1} of {playlist_length}
        </div>
      </div>
    </div>
  );
};

export default NowPlaying;