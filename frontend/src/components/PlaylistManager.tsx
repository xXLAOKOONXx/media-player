import { useState, useEffect } from 'react';
import type { User } from '../types';
import './PlaylistManager.css';

const API_BASE_URL = '';

interface PlaylistFolder {
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

interface PlaylistManagerProps {
  currentUser?: User;
}

const PlaylistManager = ({ currentUser }: PlaylistManagerProps) => {
  const [playlistFolders, setPlaylistFolders] = useState<PlaylistFolder[]>([]);
  const [playlists, setPlaylists] = useState<Playlist[]>([]);
  const [selectedFolder, setSelectedFolder] = useState<number | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [browsePath, setBrowsePath] = useState('/');
  const [browseItems, setBrowseItems] = useState<any[]>([]);
  const [editingFolder, setEditingFolder] = useState<number | null>(null);
  const [editName, setEditName] = useState('');
  const [newFolder, setNewFolder] = useState({
    name: '',
    path: '',
    type: 'playlist'
  });

  useEffect(() => {
    loadPlaylistFolders();
  }, []);

  useEffect(() => {
    if (selectedFolder) {
      loadPlaylists(selectedFolder);
    }
  }, [selectedFolder]);

  const loadPlaylistFolders = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/audio/playlists`);
      const data = await response.json();
      setPlaylistFolders(data);
    } catch (err) {
      console.error('Error loading playlist folders:', err);
    }
  };

  const loadPlaylists = async (folderId: number) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/audio/playlists/${folderId}/files`);
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

  const handleAddFolder = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await fetch(`${API_BASE_URL}/api/audio/playlists`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newFolder)
      });
      setNewFolder({ name: '', path: '', type: 'playlist' });
      setShowAddForm(false);
      loadPlaylistFolders();
    } catch (err) {
      console.error('Error adding playlist folder:', err);
    }
  };

  const handleDeleteFolder = async (folderId: number) => {
    if (!confirm('Are you sure you want to delete this playlist folder?')) {
      return;
    }
    try {
      await fetch(`${API_BASE_URL}/api/audio/playlists/${folderId}`, {
        method: 'DELETE'
      });
      if (selectedFolder === folderId) {
        setSelectedFolder(null);
        setPlaylists([]);
      }
      loadPlaylistFolders();
    } catch (err) {
      console.error('Error deleting playlist folder:', err);
      alert('Error deleting playlist folder');
    }
  };

  const handleStartRename = (folder: PlaylistFolder) => {
    setEditingFolder(folder.id);
    setEditName(folder.name);
  };

  const handleRenameFolder = async (folderId: number) => {
    if (!editName.trim()) {
      alert('Name cannot be empty');
      return;
    }
    try {
      await fetch(`${API_BASE_URL}/api/audio/playlists/${folderId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: editName })
      });
      setEditingFolder(null);
      setEditName('');
      loadPlaylistFolders();
    } catch (err) {
      console.error('Error renaming playlist folder:', err);
      alert('Error renaming playlist folder');
    }
  };

  const handleCancelRename = () => {
    setEditingFolder(null);
    setEditName('');
  };

  const handlePlayPlaylist = async (playlistPath: string) => {
    try {
      await fetch(`${API_BASE_URL}/api/audio/playback/play`, {
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
    <div className="playlist-manager">
      <div className="card">
        <div className="header-row">
          <h2>Playlist Folders</h2>
          {currentUser?.role === 'admin' && (
            <button className="btn btn-primary" onClick={() => setShowAddForm(!showAddForm)}>
              {showAddForm ? 'Cancel' : '+ Add Playlist Folder'}
            </button>
          )}
        </div>

        {showAddForm && currentUser?.role === 'admin' && (
          <form onSubmit={handleAddFolder} className="add-form">
            <div className="form-group">
              <label>Folder Name</label>
              <input
                type="text"
                value={newFolder.name}
                onChange={(e) => setNewFolder({ ...newFolder, name: e.target.value })}
                required
              />
            </div>
            <div className="form-group">
              <label>Path</label>
              <div className="path-input-group">
                <input
                  type="text"
                  value={newFolder.path}
                  onChange={(e) => setNewFolder({ ...newFolder, path: e.target.value })}
                  required
                />
                <button 
                  type="button" 
                  className="btn btn-secondary"
                  onClick={() => browsePath_fn(newFolder.path || '/')}
                >
                  Browse
                </button>
              </div>
            </div>
            {browseItems.length > 0 && (
              <div className="browse-results">
                <h4>Current Path: {browsePath}</h4>
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
                        onClick={() => {
                          if (item.is_directory) {
                            browsePath_fn(item.path);
                          } else {
                            setNewFolder({ ...newFolder, path: item.path });
                            setBrowseItems([]);
                          }
                        }}
                      >
                        <span className="material-icons">folder</span>
                        {item.name}
                      </li>
                    ))}
                </ul>
                <button
                  type="button"
                  onClick={() => {
                    setNewFolder({ ...newFolder, path: browsePath });
                    setBrowseItems([]);
                  }}
                >
                  Select Current Folder
                </button>
              </div>
            )}
            <button type="submit" className="btn btn-primary">Add Playlist Folder</button>
          </form>
        )}

        <div className="folders-list">
          {playlistFolders.length === 0 ? (
            <div className="empty-state">
              <p>No playlist folders configured</p>
              <p>Add a playlist folder to organize your playlists</p>
            </div>
          ) : (
            playlistFolders.map((folder) => (
              <div
                key={folder.id}
                className={`list-item ${selectedFolder === folder.id ? 'selected' : ''}`}
              >
                {editingFolder === folder.id ? (
                  <div className="edit-mode">
                    <input
                      type="text"
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                      className="edit-input"
                      autoFocus
                    />
                    <button className="btn btn-sm btn-primary" onClick={() => handleRenameFolder(folder.id)}>
                      Save
                    </button>
                    <button className="btn btn-sm btn-secondary" onClick={handleCancelRename}>
                      Cancel
                    </button>
                  </div>
                ) : (
                  <>
                    <div onClick={() => setSelectedFolder(folder.id)} style={{ flex: 1, cursor: 'pointer' }}>
                      <strong>{folder.name}</strong>
                      <div className="folder-path">{folder.path}</div>
                    </div>
                    {currentUser?.role === 'admin' && (
                      <div className="action-buttons">
                        <button className="btn btn-sm btn-secondary" onClick={() => handleStartRename(folder)} title="Rename">
                          ✏️
                        </button>
                        <button className="btn btn-sm btn-danger" onClick={() => handleDeleteFolder(folder.id)} title="Delete">
                          🗑️
                        </button>
                      </div>
                    )}
                  </>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      {selectedFolder && (
        <div className="card">
          <h2>Playlists</h2>
          <div className="playlists-list">
            {playlists.length === 0 ? (
              <div className="empty-state">
                <p>No playlists found in this folder</p>
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

export default PlaylistManager;