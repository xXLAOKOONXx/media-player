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
      await fetch(`${API_BASE_URL}/api/audio/playback/play`, {
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
      await fetch(`${API_BASE_URL}/api/audio/playback/pause`, {
        method: 'POST'
      });
      onUpdate();
    } catch (err) {
      console.error('Error pausing:', err);
    }
  };

  const handleStop = async () => {
    try {
      await fetch(`${API_BASE_URL}/api/audio/playback/stop`, {
        method: 'POST'
      });
      onUpdate();
    } catch (err) {
      console.error('Error stopping:', err);
    }
  };

  const handlePrevious = async () => {
    try {
      await fetch(`${API_BASE_URL}/api/audio/playback/previous`, {
        method: 'POST'
      });
      onUpdate();
    } catch (err) {
      console.error('Error going to previous:', err);
    }
  };

  const handleNext = async () => {
    try {
      await fetch(`${API_BASE_URL}/api/audio/playback/next`, {
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
      await fetch(`${API_BASE_URL}/api/audio/playback/volume`, {
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
      await fetch(`${API_BASE_URL}/api/audio/playback/shuffle`, {
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
      await fetch(`${API_BASE_URL}/api/audio/playback/repeat`, {
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
    </div>
  );
};

export default PlaybackControls;