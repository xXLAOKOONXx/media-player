import React, { useState, useEffect } from 'react';
import './LibraryManager.css';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

interface Library {
  id: number;
  name: string;
  type: string;
  path: string;
  storage_id?: number;
}

interface Playlist {
  name: string;
  path: string;
  size: number;
}

const LibraryManager: React.FC = () => {
  const [libraries, setLibraries] = useState<Library[]>([]);
  const [playlists, setPlaylists] = useState<Playlist[]>([]);
  const [selectedLibrary, setSelectedLibrary] = useState<number | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [browsePath, setBrowsePath] = useState('/');
  const [browseItems, setBrowseItems] = useState<any[]>([]);
  const [newLibrary, setNewLibrary] = useState({
    name: '',
    path: '',
    type: 'playlist'
  });

  useEffect(() => {
    loadLibraries();
  }, []);

  useEffect(() => {
    if (selectedLibrary) {
      loadPlaylists(selectedLibrary);
    }
  }, [selectedLibrary]);

  const loadLibraries = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/libraries`);
      const data = await response.json();
      setLibraries(data);
    } catch (err) {
      console.error('Error loading libraries:', err);
    }
  };

  const loadPlaylists = async (libraryId: number) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/libraries/${libraryId}/playlists`);
      const data = await response.json();
      setPlaylists(data);
    } catch (err) {
      console.error('Error loading playlists:', err);
    }
  };

  const browsePath_fn = async (path: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/browse`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path })
      });
      const data = await response.json();
      setBrowseItems(data.items || []);
      setBrowsePath(data.current_path || path);
    } catch (err) {
      console.error('Error browsing path:', err);
    }
  };

  const handleAddLibrary = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await fetch(`${API_BASE_URL}/api/libraries`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newLibrary)
      });
      setNewLibrary({ name: '', path: '', type: 'playlist' });
      setShowAddForm(false);
      loadLibraries();
    } catch (err) {
      console.error('Error adding library:', err);
    }
  };

  const handlePlayPlaylist = async (playlistPath: string) => {
    try {
      await fetch(`${API_BASE_URL}/api/playback/play`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ playlist_path: playlistPath, track_index: 0 })
      });
      alert('Playlist started!');
    } catch (err) {
      console.error('Error playing playlist:', err);
      alert('Error playing playlist');
    }
  };

  return (
    <div className="library-manager">
      <div className="card">
        <div className="header-row">
          <h2>Libraries</h2>
          <button className="btn btn-primary" onClick={() => setShowAddForm(!showAddForm)}>
            {showAddForm ? 'Cancel' : '+ Add Library'}
          </button>
        </div>

        {showAddForm && (
          <form onSubmit={handleAddLibrary} className="add-form">
            <div className="form-group">
              <label>Library Name</label>
              <input
                type="text"
                value={newLibrary.name}
                onChange={(e) => setNewLibrary({ ...newLibrary, name: e.target.value })}
                required
              />
            </div>
            <div className="form-group">
              <label>Path</label>
              <div className="path-input-group">
                <input
                  type="text"
                  value={newLibrary.path}
                  onChange={(e) => setNewLibrary({ ...newLibrary, path: e.target.value })}
                  required
                />
                <button 
                  type="button" 
                  className="btn btn-secondary"
                  onClick={() => browsePath_fn(newLibrary.path || '/')}
                >
                  Browse
                </button>
              </div>
            </div>
            {browseItems.length > 0 && (
              <div className="browse-results">
                <p><strong>Current: {browsePath}</strong></p>
                <div className="browse-items">
                  {browseItems.map((item, idx) => (
                    <div
                      key={idx}
                      className="browse-item"
                      onClick={() => {
                        if (item.is_directory) {
                          browsePath_fn(item.path);
                        } else {
                          setNewLibrary({ ...newLibrary, path: item.path });
                        }
                      }}
                    >
                      {item.is_directory ? '📁' : item.is_playlist ? '🎵' : '📄'} {item.name}
                    </div>
                  ))}
                </div>
              </div>
            )}
            <button type="submit" className="btn btn-primary">Add Library</button>
          </form>
        )}

        <div className="libraries-list">
          {libraries.length === 0 ? (
            <div className="empty-state">
              <p>No libraries configured</p>
              <p>Add a library to organize your playlists</p>
            </div>
          ) : (
            libraries.map((lib) => (
              <div
                key={lib.id}
                className={`list-item ${selectedLibrary === lib.id ? 'selected' : ''}`}
                onClick={() => setSelectedLibrary(lib.id)}
              >
                <div>
                  <strong>{lib.name}</strong>
                  <div className="library-path">{lib.path}</div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {selectedLibrary && (
        <div className="card">
          <h2>Playlists</h2>
          <div className="playlists-list">
            {playlists.length === 0 ? (
              <div className="empty-state">
                <p>No playlists found in this library</p>
              </div>
            ) : (
              playlists.map((playlist, idx) => (
                <div key={idx} className="list-item playlist-item">
                  <div>
                    <strong>🎵 {playlist.name}</strong>
                    <div className="playlist-path">{playlist.path}</div>
                  </div>
                  <button
                    className="btn btn-primary"
                    onClick={() => handlePlayPlaylist(playlist.path)}
                  >
                    Play
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default LibraryManager;