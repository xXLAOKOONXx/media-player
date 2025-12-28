import { useState, useEffect } from 'react';
import type { User } from '../types';
import './SoundEffectsManager.css';

const API_BASE_URL = '';

interface SoundEffectsFolder {
  id: number;
  name: string;
  path: string;
  storage_id?: number;
}

interface AudioFile {
  name: string;
  path: string;
  size: number;
  extension: string;
}

interface SoundEffectsManagerProps {
  currentUser?: User;
}

const SoundEffectsManager = ({ currentUser }: SoundEffectsManagerProps) => {
  const [soundEffectsFolders, setSoundEffectsFolders] = useState<SoundEffectsFolder[]>([]);
  const [audioFiles, setAudioFiles] = useState<AudioFile[]>([]);
  const [selectedFolder, setSelectedFolder] = useState<number | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [browsePath, setBrowsePath] = useState('/');
  const [browseItems, setBrowseItems] = useState<any[]>([]);
  const [editingFolder, setEditingFolder] = useState<number | null>(null);
  const [editName, setEditName] = useState('');
  const [newFolder, setNewFolder] = useState({
    name: '',
    path: ''
  });

  useEffect(() => {
    loadSoundEffectsFolders();
  }, []);

  useEffect(() => {
    if (selectedFolder) {
      loadAudioFiles(selectedFolder);
    }
  }, [selectedFolder]);

  const loadSoundEffectsFolders = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/audio/soundeffects`);
      const data = await response.json();
      setSoundEffectsFolders(data);
    } catch (err) {
      console.error('Error loading sound effects folders:', err);
    }
  };

  const loadAudioFiles = async (folderId: number) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/audio/soundeffects/${folderId}/files`);
      const data = await response.json();
      setAudioFiles(data);
    } catch (err) {
      console.error('Error loading audio files:', err);
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
      await fetch(`${API_BASE_URL}/api/audio/soundeffects`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newFolder)
      });
      setNewFolder({ name: '', path: '' });
      setShowAddForm(false);
      loadSoundEffectsFolders();
    } catch (err) {
      console.error('Error adding sound effects folder:', err);
    }
  };

  const handleDeleteFolder = async (folderId: number) => {
    if (!window.confirm('Are you sure you want to delete this sound effects folder?')) {
      return;
    }
    try {
      await fetch(`${API_BASE_URL}/api/audio/soundeffects/${folderId}`, {
        method: 'DELETE'
      });
      if (selectedFolder === folderId) {
        setSelectedFolder(null);
        setAudioFiles([]);
      }
      loadSoundEffectsFolders();
    } catch (err) {
      console.error('Error deleting sound effects folder:', err);
      alert('Error deleting sound effects folder');
    }
  };

  const handleStartRename = (folder: SoundEffectsFolder) => {
    setEditingFolder(folder.id);
    setEditName(folder.name);
  };

  const handleRenameFolder = async (folderId: number) => {
    if (!editName.trim()) {
      alert('Name cannot be empty');
      return;
    }
    try {
      await fetch(`${API_BASE_URL}/api/audio/soundeffects/${folderId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: editName })
      });
      setEditingFolder(null);
      setEditName('');
      loadSoundEffectsFolders();
    } catch (err) {
      console.error('Error renaming sound effects folder:', err);
      alert('Error renaming sound effects folder');
    }
  };

  const handleCancelRename = () => {
    setEditingFolder(null);
    setEditName('');
  };

  const handlePlaySoundEffect = async (soundPath: string) => {
    try {
      await fetch(`${API_BASE_URL}/api/audio/soundeffects/play`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sound_path: soundPath })
      });
    } catch (err) {
      console.error('Error playing sound effect:', err);
      alert('Error playing sound effect');
    }
  };

  return (
    <div className="sound-effects-manager">
      <div className="card">
        <div className="header-row">
          <h2>Sound Effects Folders</h2>
          {currentUser?.role === 'admin' && (
            <button className="btn btn-primary" onClick={() => setShowAddForm(!showAddForm)}>
              {showAddForm ? 'Cancel' : '+ Add Sound Effects Folder'}
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
                          setNewFolder({ ...newFolder, path: item.path });
                        }
                      }}
                    >
                      {item.is_directory ? '📁' : '📄'} {item.name}
                    </div>
                  ))}
                </div>
              </div>
            )}
            <button type="submit" className="btn btn-primary">Add Sound Effects Folder</button>
          </form>
        )}

        <div className="folders-list">
          {soundEffectsFolders.length === 0 ? (
            <div className="empty-state">
              <p>No sound effects folders configured</p>
              <p>Add a sound effects folder to play audio effects alongside your music</p>
            </div>
          ) : (
            soundEffectsFolders.map((folder) => (
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
          <h2>Audio Files</h2>
          <div className="audio-files-list">
            {audioFiles.length === 0 ? (
              <div className="empty-state">
                <p>No audio files found in this folder</p>
                <p>Supported formats: MP3, WAV, OGG, FLAC, M4A, AAC</p>
              </div>
            ) : (
              audioFiles.map((file, idx) => (
                <div key={idx} className="list-item audio-file-item">
                  <div>
                    <strong>🔊 {file.name}</strong>
                    <div className="file-info">
                      {file.extension.toUpperCase()} • {(file.size / 1024).toFixed(1)} KB
                    </div>
                  </div>
                  <button
                    className="btn btn-primary"
                    onClick={() => handlePlaySoundEffect(file.path)}
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

export default SoundEffectsManager;
