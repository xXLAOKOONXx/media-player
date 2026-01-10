import { useState, useEffect } from 'react';
import './VideoPlaybackControls.css';

const API_BASE_URL = '';

interface VideoPlaybackControlsProps {
  status: any;
  onUpdate: () => void;
}

const VideoPlaybackControls = ({ status, onUpdate }: VideoPlaybackControlsProps) => {
  const [volume, setVolume] = useState(status?.volume || 50);

  // Sync volume state with status prop when it changes
  useEffect(() => {
    if (typeof status?.volume === 'number') {
      setVolume(status.volume);
    }
  }, [status?.volume]);

  const audioTracks = Array.isArray(status?.audio_tracks) ? status.audio_tracks : [];
  const subtitleTracks = Array.isArray(status?.subtitle_tracks) ? status.subtitle_tracks : [];

  const selectableAudioTracks = audioTracks.filter((t: any) => typeof t?.id === 'number');
  const selectableSubtitleTracks = subtitleTracks.filter((t: any) => typeof t?.id === 'number');

  const showAudioTrackSelect = selectableAudioTracks.length > 1;
  const subtitleRealCount = selectableSubtitleTracks.filter((t: any) => (t?.id ?? 0) >= 0).length;
  const showSubtitleSelect = subtitleRealCount > 1;

  const canSaveDefaults = (showAudioTrackSelect || showSubtitleSelect) && typeof status?.current_track?.media_id === 'string';

  const currentAudioTrackId = typeof status?.current_audio_track_id === 'number' ? status.current_audio_track_id : undefined;
  const currentSubtitleTrackId = typeof status?.current_subtitle_track_id === 'number' ? status.current_subtitle_track_id : -1;

  const handlePlay = async () => {
    try {
      await fetch(`${API_BASE_URL}/api/video/playback/play`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });
      onUpdate();
    } catch (err) {
      console.error('Error playing:', err);
    }
  };

  const handlePause = async () => {
    try {
      await fetch(`${API_BASE_URL}/api/video/playback/pause`, {
        method: 'POST'
      });
      onUpdate();
    } catch (err) {
      console.error('Error pausing:', err);
    }
  };

  const handleStop = async () => {
    try {
      await fetch(`${API_BASE_URL}/api/video/playback/stop`, {
        method: 'POST'
      });
      onUpdate();
    } catch (err) {
      console.error('Error stopping:', err);
    }
  };

  const handlePrevious = async () => {
    try {
      await fetch(`${API_BASE_URL}/api/video/playback/previous`, {
        method: 'POST'
      });
      onUpdate();
    } catch (err) {
      console.error('Error going to previous:', err);
    }
  };

  const handleNext = async () => {
    try {
      await fetch(`${API_BASE_URL}/api/video/playback/next`, {
        method: 'POST'
      });
      onUpdate();
    } catch (err) {
      console.error('Error going to next:', err);
    }
  };

  const handleVolumeChange = async (newVolume: number) => {
    setVolume(newVolume);
    try {
      await fetch(`${API_BASE_URL}/api/video/playback/volume`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ volume: newVolume })
      });
    } catch (err) {
      console.error('Error setting volume:', err);
    }
  };

  const handleVolumeDecrease = () => {
    const newVolume = Math.max(0, volume - 1);
    handleVolumeChange(newVolume);
  };

  const handleVolumeIncrease = () => {
    const newVolume = Math.min(100, volume + 1);
    handleVolumeChange(newVolume);
  };

  const handleShuffle = async () => {
    const newShuffleState = !status?.shuffle;
    try {
      await fetch(`${API_BASE_URL}/api/video/playback/shuffle`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: newShuffleState })
      });
      onUpdate();
    } catch (err) {
      console.error('Error toggling shuffle:', err);
    }
  };

  const handleRepeatMode = async () => {
    const modes = ['none', 'all', 'one'];
    const currentMode = status?.repeat_mode || 'none';
    const currentIndex = modes.indexOf(currentMode);
    const nextMode = modes[(currentIndex + 1) % modes.length];
    
    try {
      await fetch(`${API_BASE_URL}/api/video/playback/repeat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: nextMode })
      });
      onUpdate();
    } catch (err) {
      console.error('Error changing repeat mode:', err);
    }
  };

  const getRepeatIcon = () => {
    const mode = status?.repeat_mode || 'none';
    switch (mode) {
      case 'all': return 'repeat';
      case 'one': return 'repeat_one';
      default: return 'repeat';
    }
  };

  const getRepeatTitle = () => {
    const mode = status?.repeat_mode || 'none';
    switch (mode) {
      case 'all': return 'Repeat: All';
      case 'one': return 'Repeat: One';
      default: return 'Repeat: Off';
    }
  };

  const isPlaying = status?.is_playing && !status?.is_paused;
  const shuffleEnabled = status?.shuffle || false;

  const handleAudioTrackChange = async (trackId: number) => {
    try {
      await fetch(`${API_BASE_URL}/api/video/playback/audio-track`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ track_id: trackId })
      });
      onUpdate();
    } catch (err) {
      console.error('Error selecting audio track:', err);
    }
  };

  const handleSubtitleTrackChange = async (trackId: number) => {
    try {
      await fetch(`${API_BASE_URL}/api/video/playback/subtitle-track`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ track_id: trackId })
      });
      onUpdate();
    } catch (err) {
      console.error('Error selecting subtitle track:', err);
    }
  };

  const handleSaveDefaultChannels = async () => {
    try {
      await fetch(`${API_BASE_URL}/api/video/playback/save-default-channels`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });
      onUpdate();
    } catch (err) {
      console.error('Error saving default channels:', err);
    }
  };

  return (
    <div className="playback-controls card">
      <h2>Controls</h2>
      
      <div className="mode-controls">
        <button 
          className={`control-btn ${shuffleEnabled ? 'active' : ''}`} 
          onClick={handleShuffle} 
          title={shuffleEnabled ? 'Shuffle: On' : 'Shuffle: Off'}
        >
          <span className="material-icons">shuffle</span>
        </button>
        
        <button 
          className={`control-btn ${status?.repeat_mode !== 'none' ? 'active' : ''}`}
          onClick={handleRepeatMode}
          title={getRepeatTitle()}
        >
          <span className="material-icons">{getRepeatIcon()}</span>
        </button>
      </div>
      
      <div className="transport-controls">
        <button className="control-btn" onClick={handlePrevious} title="Previous">
          <span className="material-icons">skip_previous</span>
        </button>
        
        {!isPlaying ? (
          <button className="control-btn play-btn" onClick={handlePlay} title="Play">
            <span className="material-icons">play_arrow</span>
          </button>
        ) : (
          <button className="control-btn pause-btn" onClick={handlePause} title="Pause">
            <span className="material-icons">pause</span>
          </button>
        )}
        
        <button className="control-btn" onClick={handleStop} title="Stop">
          <span className="material-icons">stop</span>
        </button>
        
        <button className="control-btn" onClick={handleNext} title="Next">
          <span className="material-icons">skip_next</span>
        </button>
      </div>

      <div className="volume-control">
        <span className="material-icons volume-icon">volume_up</span>
        <button 
          className="volume-btn" 
          onClick={handleVolumeDecrease}
          disabled={volume === 0}
          title="Decrease volume by 1%"
        >
          <span className="material-icons">remove</span>
        </button>
        <input
          type="range"
          min="0"
          max="100"
          value={volume}
          onChange={(e) => handleVolumeChange(parseInt(e.target.value))}
          className="volume-slider"
        />
        <button 
          className="volume-btn" 
          onClick={handleVolumeIncrease}
          disabled={volume === 100}
          title="Increase volume by 1%"
        >
          <span className="material-icons">add</span>
        </button>
        <span className="volume-value">{volume}%</span>
      </div>

      {(showAudioTrackSelect || showSubtitleSelect) && (
        <div className="track-select-control">
          {showAudioTrackSelect && (
            <label className="track-select-field">
              <span className="track-select-label">Audio</span>
              <select
                className="track-select"
                value={currentAudioTrackId ?? selectableAudioTracks[0]?.id}
                onChange={(e) => handleAudioTrackChange(parseInt(e.target.value, 10))}
              >
                {selectableAudioTracks.map((t: any) => (
                  <option key={t.id} value={t.id}>
                    {t.label || `Audio ${t.id}`}
                  </option>
                ))}
              </select>
            </label>
          )}

          {showSubtitleSelect && (
            <label className="track-select-field">
              <span className="track-select-label">Subtitles</span>
              <select
                className="track-select"
                value={currentSubtitleTrackId}
                onChange={(e) => handleSubtitleTrackChange(parseInt(e.target.value, 10))}
              >
                {selectableSubtitleTracks.map((t: any) => (
                  <option key={t.id} value={t.id}>
                    {t.label || (t.id < 0 ? 'Off' : `Sub ${t.id}`)}
                  </option>
                ))}
              </select>
            </label>
          )}

          <button
            className="control-btn"
            onClick={handleSaveDefaultChannels}
            disabled={!canSaveDefaults}
            title={canSaveDefaults ? 'Save Default channels' : 'Start a video to save defaults'}
          >
            Save Default channels
          </button>
        </div>
      )}
    </div>
  );
};

export default VideoPlaybackControls;