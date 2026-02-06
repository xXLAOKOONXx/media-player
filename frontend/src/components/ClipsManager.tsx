import './ClipsManager.css';
import { useState, useEffect } from 'react';
import type { User } from '../types';

const API_BASE_URL = '';

interface Clip {
  id: number;
  clip_media_id: string;
  source_media_id: string;
  source_file_path: string;
  source_series_name: string;
  clip_file_path: string;
  clip_file_name: string;
  clip_duration: number;
  source_position: number;
  created_at: number;
  user_id: number;
  audio_track_id: number;
  subtitle_track_id: number;
}

interface BrowseItem {
  name: string;
  path: string;
  is_directory: boolean;
}

interface ClipsManagerProps {
  currentUser: User;
}

const ClipsManager = ({ currentUser }: ClipsManagerProps) => {
  const [clips, setClips] = useState<Clip[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [clipsFolder, setClipsFolder] = useState('');
  const [showFolderModal, setShowFolderModal] = useState(false);
  const [newFolderPath, setNewFolderPath] = useState('');
  const [browsePath, setBrowsePath] = useState('/');
  const [browseItems, setBrowseItems] = useState<BrowseItem[]>([]);
  const [isBrowsing, setIsBrowsing] = useState(false);

  const isAdmin = currentUser?.role === 'admin';

  useEffect(() => {
    loadClips();
    loadClipsFolder();
  }, []);

  const loadClips = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/video/clips`, {
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error('Failed to load clips');
      }

      const data = await response.json();
      setClips(data.clips || []);
    } catch (err) {
      console.error('Error loading clips:', err);
      setError('Failed to load clips');
    } finally {
      setLoading(false);
    }
  };

  const loadClipsFolder = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/video/clips/folder`, {
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();
        setClipsFolder(data.folder || '');
        setNewFolderPath(data.folder || '');
      }
    } catch (err) {
      console.error('Error loading clips folder:', err);
    }
  };

  const browsePath_fn = async (path: string) => {
    try {
      setIsBrowsing(true);
      const response = await fetch(`${API_BASE_URL}/api/browse`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ path })
      });
      const data = await response.json();
      setBrowseItems(data.items || []);
      setBrowsePath(data.current_path || path);
    } catch (err) {
      console.error('Error browsing path:', err);
    } finally {
      setIsBrowsing(false);
    }
  };

  const deleteClip = async (clipMediaId: string) => {
    if (!confirm('Are you sure you want to delete this clip?')) {
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/video/clips/${clipMediaId}`, {
        method: 'DELETE',
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error('Failed to delete clip');
      }

      // Reload clips after successful deletion
      await loadClips();
    } catch (err) {
      console.error('Error deleting clip:', err);
      alert('Failed to delete clip');
    }
  };

  const handleOpenFolderModal = () => {
    setNewFolderPath(clipsFolder);
    setBrowseItems([]);
    setShowFolderModal(true);
  };

  const handleCloseFolderModal = () => {
    setShowFolderModal(false);
    setBrowseItems([]);
    setNewFolderPath(clipsFolder);
  };

  const saveClipsFolder = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/video/clips/folder`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ folder: newFolderPath })
      });

      if (!response.ok) {
        throw new Error('Failed to update clips folder');
      }

      setClipsFolder(newFolderPath);
      setShowFolderModal(false);
      setBrowseItems([]);
    } catch (err) {
      console.error('Error updating clips folder:', err);
      alert('Failed to update clips folder');
    }
  };

  const formatDate = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleString();
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatDuration = formatTime;
  const formatPosition = formatTime;

  return (
    <div className="clips-manager">
      <div className="clips-header card">
        <h2>Video Clips</h2>
        <p className="clips-description">
          Manage your 60-second video clips created from the Player tab.
        </p>

        <div className="clips-folder-section">
          <div className="clips-folder-info">
            <span className="material-icons">folder</span>
            <span className="clips-folder-label">Clips Folder:</span>
            <span className="clips-folder-path">{clipsFolder || 'Not set'}</span>
          </div>
          {isAdmin && (
            <div className="clips-folder-actions">
              <button
                className="btn btn-secondary btn-sm"
                onClick={handleOpenFolderModal}
              >
                <span className="material-icons">edit</span>
                Edit
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="clips-list card">
        <h3>Your Clips ({clips.length})</h3>

        {loading && (
          <div className="clips-loading">
            <span className="material-icons spinning">refresh</span>
            Loading clips...
          </div>
        )}

        {error && (
          <div className="clips-error">
            <span className="material-icons">error</span>
            {error}
          </div>
        )}

        {!loading && !error && clips.length === 0 && (
          <div className="clips-empty">
            <span className="material-icons">content_cut</span>
            <p>No clips yet</p>
            <p className="clips-empty-hint">
              Go to the Player tab and click the scissors icon to create a 60-second clip
            </p>
          </div>
        )}

        {!loading && !error && clips.length > 0 && (
          <div className="clips-grid">
            {clips.map((clip) => (
              <div key={clip.clip_media_id} className="clip-card">
                <div className="clip-header">
                  <span className="material-icons clip-icon">content_cut</span>
                  <div className="clip-title-section">
                    <h4 className="clip-title">{clip.clip_file_name}</h4>
                    {clip.source_series_name && (
                      <span className="clip-series">
                        <span className="material-icons">tv</span>
                        {clip.source_series_name}
                      </span>
                    )}
                  </div>
                </div>

                <div className="clip-details">
                  <div className="clip-detail-row">
                    <span className="material-icons">schedule</span>
                    <span>Duration: {formatDuration(clip.clip_duration)}</span>
                  </div>
                  <div className="clip-detail-row">
                    <span className="material-icons">fast_rewind</span>
                    <span>From position: {formatPosition(clip.source_position)}</span>
                  </div>
                  <div className="clip-detail-row">
                    <span className="material-icons">calendar_today</span>
                    <span>{formatDate(clip.created_at)}</span>
                  </div>
                </div>

                <div className="clip-actions">
                  <a
                    href={`${API_BASE_URL}/api/video/clips/stream/${clip.clip_media_id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn btn-primary btn-sm"
                    title="Play clip"
                  >
                    <span className="material-icons">play_arrow</span>
                    Play
                  </a>
                  <button
                    className="btn btn-danger btn-sm"
                    onClick={() => deleteClip(clip.clip_media_id)}
                    title="Delete clip"
                  >
                    <span className="material-icons">delete</span>
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {showFolderModal && (
        <div className="modal">
          <div className="modal-content">
            <h3>Configure Clips Folder</h3>
            <form onSubmit={(e) => { e.preventDefault(); saveClipsFolder(); }}>
              <div className="form-group">
                <label>Clips Folder Path:</label>
                <div className="path-input-group">
                  <input
                    type="text"
                    value={newFolderPath}
                    onChange={(e) => setNewFolderPath(e.target.value)}
                    required
                  />
                  <button
                    type="button"
                    onClick={() => browsePath_fn(newFolderPath || '/')}
                  >
                    Browse
                  </button>
                </div>
              </div>

              {browseItems.length > 0 && (
                <div className="browse-results">
                  <h4>Current Path: {browsePath}</h4>
                  {isBrowsing ? (
                    <div className="loading">Loading...</div>
                  ) : (
                    <>
                      <ul>
                        <li onClick={() => browsePath_fn(browsePath + '/..')}>
                          <span className="material-icons">folder</span>
                          ..
                        </li>
                        {browseItems
                          .filter(item => item.is_directory)
                          .map((item, idx) => (
                            <li
                              key={idx}
                              onClick={() => browsePath_fn(item.path)}
                            >
                              <span className="material-icons">folder</span>
                              {item.name}
                            </li>
                          ))}
                      </ul>
                      <button
                        type="button"
                        onClick={() => {
                          setNewFolderPath(browsePath);
                          setBrowseItems([]);
                        }}
                      >
                        Select Current Folder
                      </button>
                    </>
                  )}
                </div>
              )}

              <div className="form-actions">
                <button type="submit">Save</button>
                <button type="button" onClick={handleCloseFolderModal}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default ClipsManager;
