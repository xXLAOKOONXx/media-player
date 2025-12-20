import { useState } from 'react';
import './PlaybackControls.css';

const API_BASE_URL = '';

interface PlaybackControlsProps {
  status: any;
  onUpdate: () => void;
}

const PlaybackControls = ({ status, onUpdate }: PlaybackControlsProps) => {
  const [volume, setVolume] = useState(status?.volume || 50);

  const handlePlay = async () => {
    try {
      await fetch(`${API_BASE_URL}/api/playback/play`, {
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
      await fetch(`${API_BASE_URL}/api/playback/pause`, {
        method: 'POST'
      });
      onUpdate();
    } catch (err) {
      console.error('Error pausing:', err);
    }
  };

  const handleStop = async () => {
    try {
      await fetch(`${API_BASE_URL}/api/playback/stop`, {
        method: 'POST'
      });
      onUpdate();
    } catch (err) {
      console.error('Error stopping:', err);
    }
  };

  const handlePrevious = async () => {
    try {
      await fetch(`${API_BASE_URL}/api/playback/previous`, {
        method: 'POST'
      });
      onUpdate();
    } catch (err) {
      console.error('Error going to previous:', err);
    }
  };

  const handleNext = async () => {
    try {
      await fetch(`${API_BASE_URL}/api/playback/next`, {
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
      await fetch(`${API_BASE_URL}/api/playback/volume`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ volume: newVolume })
      });
    } catch (err) {
      console.error('Error setting volume:', err);
    }
  };

  const isPlaying = status?.is_playing && !status?.is_paused;

  return (
    <div className="playback-controls card">
      <h2>Controls</h2>
      
      <div className="transport-controls">
        <button className="control-btn" onClick={handlePrevious} title="Previous">
          ⏮
        </button>
        
        {!isPlaying ? (
          <button className="control-btn play-btn" onClick={handlePlay} title="Play">
            ▶
          </button>
        ) : (
          <button className="control-btn pause-btn" onClick={handlePause} title="Pause">
            ⏸
          </button>
        )}
        
        <button className="control-btn" onClick={handleStop} title="Stop">
          ⏹
        </button>
        
        <button className="control-btn" onClick={handleNext} title="Next">
          ⏭
        </button>
      </div>

      <div className="volume-control">
        <span className="volume-icon">🔊</span>
        <input
          type="range"
          min="0"
          max="100"
          value={volume}
          onChange={(e) => handleVolumeChange(parseInt(e.target.value))}
          className="volume-slider"
        />
        <span className="volume-value">{volume}%</span>
      </div>
    </div>
  );
};

export default PlaybackControls;