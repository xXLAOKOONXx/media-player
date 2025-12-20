import { useState, useEffect } from 'react';
import './TrackTimesEditor.css';

const API_BASE_URL = '';

interface Track {
  index: number;
  title: string;
  path: string;
  duration: string;
  start_time: number | null;
  end_time: number | null;
}

const TrackTimesEditor = () => {
  const [tracks, setTracks] = useState<Track[]>([]);
  const [editingTrack, setEditingTrack] = useState<number | null>(null);
  const [startTime, setStartTime] = useState<string>('');
  const [endTime, setEndTime] = useState<string>('');
  const [error, setError] = useState<string>('');

  const loadTracks = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/playback/tracks`);
      const data = await response.json();
      setTracks(data.tracks || []);
    } catch (err) {
      console.error('Error loading tracks:', err);
    }
  };

  useEffect(() => {
    loadTracks();
    // Refresh tracks every 10 seconds when tab is visible
    const interval = setInterval(() => {
      if (!document.hidden) {
        loadTracks();
      }
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  const formatTime = (seconds: number | null) => {
    if (seconds == null) return '';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const parseTime = (timeStr: string): number | null => {
    if (!timeStr || timeStr.trim() === '') return null;
    
    const parts = timeStr.split(':');
    if (parts.length === 2) {
      const mins = parseInt(parts[0]);
      const secs = parseInt(parts[1]);
      if (!isNaN(mins) && !isNaN(secs)) {
        return mins * 60 + secs;
      }
    }
    
    const seconds = parseFloat(timeStr);
    if (!isNaN(seconds)) {
      return seconds;
    }
    
    return null;
  };

  const handleEdit = (track: Track) => {
    setEditingTrack(track.index);
    setStartTime(formatTime(track.start_time));
    setEndTime(formatTime(track.end_time));
    setError('');
  };

  const handleSave = async (trackIndex: number) => {
    try {
      setError('');
      
      const parsedStartTime = parseTime(startTime);
      const parsedEndTime = parseTime(endTime);
      
      if (parsedStartTime !== null && parsedStartTime < 0) {
        setError('Start time must be non-negative');
        return;
      }
      
      if (parsedEndTime !== null && parsedEndTime < 0) {
        setError('End time must be non-negative');
        return;
      }
      
      if (parsedStartTime !== null && parsedEndTime !== null && parsedStartTime >= parsedEndTime) {
        setError('Start time must be less than end time');
        return;
      }
      
      const response = await fetch(`${API_BASE_URL}/api/playback/tracks/${trackIndex}/times`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          start_time: parsedStartTime,
          end_time: parsedEndTime
        })
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Failed to save track times' }));
        setError(errorData.error || 'Failed to save track times');
        return;
      }
      
      setEditingTrack(null);
      setStartTime('');
      setEndTime('');
      loadTracks();
    } catch (err) {
      console.error('Error saving track times:', err);
      setError('Failed to save track times');
    }
  };

  const handleCancel = () => {
    setEditingTrack(null);
    setStartTime('');
    setEndTime('');
    setError('');
  };

  const handleClear = async (trackIndex: number) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/playback/tracks/${trackIndex}/times`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          start_time: null,
          end_time: null
        })
      });
      
      if (!response.ok) {
        console.error('Failed to clear track times');
        alert('Failed to clear track times');
        return;
      }
      
      loadTracks();
    } catch (err) {
      console.error('Error clearing track times:', err);
      alert('Error clearing track times');
    }
  };

  if (tracks.length === 0) {
    return (
      <div className="track-times-editor card">
        <h2>Track Times</h2>
        <div className="empty-state">
          <p>No playlist loaded</p>
          <p>Load a playlist to edit track start and end times</p>
        </div>
      </div>
    );
  }

  return (
    <div className="track-times-editor card">
      <h2>Track Times</h2>
      <p className="info-text">
        Set custom start and end times for each track. Leave empty to use the full track.
        Format: MM:SS or seconds
      </p>
      
      <div className="tracks-list">
        {tracks.map((track) => (
          <div key={track.index} className="track-item">
            {editingTrack === track.index ? (
              <div className="edit-form">
                <div className="track-header">
                  <strong>{track.title}</strong>
                </div>
                <div className="time-inputs">
                  <div className="input-group">
                    <label>Start Time:</label>
                    <input
                      type="text"
                      value={startTime}
                      onChange={(e) => setStartTime(e.target.value)}
                      placeholder="0:00 or empty"
                    />
                  </div>
                  <div className="input-group">
                    <label>End Time:</label>
                    <input
                      type="text"
                      value={endTime}
                      onChange={(e) => setEndTime(e.target.value)}
                      placeholder="Leave empty for end"
                    />
                  </div>
                </div>
                {error && <div className="error-message">{error}</div>}
                <div className="button-group">
                  <button className="btn btn-primary" onClick={() => handleSave(track.index)}>
                    Save
                  </button>
                  <button className="btn btn-secondary" onClick={handleCancel}>
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <div className="track-display">
                <div className="track-header">
                  <strong>#{track.index + 1}: {track.title}</strong>
                  <span className="track-duration">
                    {track.duration !== 'Unknown' ? `Duration: ${track.duration}s` : ''}
                  </span>
                </div>
                <div className="track-times">
                  {track.start_time != null || track.end_time != null ? (
                    <span className="custom-times">
                      📌 Custom: {formatTime(track.start_time) || '0:00'} - {formatTime(track.end_time) || 'end'}
                    </span>
                  ) : (
                    <span className="no-custom-times">No custom times set</span>
                  )}
                </div>
                <div className="button-group">
                  <button className="btn btn-small" onClick={() => handleEdit(track)}>
                    Edit
                  </button>
                  {(track.start_time != null || track.end_time != null) && (
                    <button className="btn btn-small btn-secondary" onClick={() => handleClear(track.index)}>
                      Clear
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default TrackTimesEditor;
