import { useState, useEffect } from 'react';
import type { User } from '../types';
import './MusicManager.css';

const API_BASE_URL = '';

interface MusicFolder {
  id: number;
  name: string;
  path: string;
  recursive: boolean;
  storage_id?: number;
}

interface Track {
  name: string;
  path: string;
  media_id?: string;
  size: number;
  artist?: string;
  title?: string;
  album?: string;
  duration?: number;
  tags?: string[];
}

interface Playlist {
  name: string;
  path: string;
}

interface BrowseItem {
  name: string;
  path: string;
  is_directory: boolean;
  is_playlist?: boolean;
}

interface MusicManagerProps {
  currentUser?: User;
}

const MusicManager = ({ currentUser }: MusicManagerProps) => {
  const [musicFolders, setMusicFolders] = useState<MusicFolder[]>([]);
  const [tracks, setTracks] = useState<Track[]>([]);
  const [filteredTracks, setFilteredTracks] = useState<Track[]>([]);
  const [selectedFolder, setSelectedFolder] = useState<number | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [browsePath, setBrowsePath] = useState('/');
  const [browseItems, setBrowseItems] = useState<BrowseItem[]>([]);
  const [editingFolder, setEditingFolder] = useState<number | null>(null);
  const [editName, setEditName] = useState('');
  const [playlistFolder, setPlaylistFolder] = useState('');
  const [showPlaylistFolderForm, setShowPlaylistFolderForm] = useState(false);
  const [showCreatePlaylistForm, setShowCreatePlaylistForm] = useState(false);
  const [newPlaylistName, setNewPlaylistName] = useState('');
  const [selectedTracks, setSelectedTracks] = useState<Set<string>>(new Set());
  const [availablePlaylists, setAvailablePlaylists] = useState<Playlist[]>([]);
  const [showAddToPlaylistForm, setShowAddToPlaylistForm] = useState(false);
  const [selectedPlaylist, setSelectedPlaylist] = useState('');
  const [trackToAdd, setTrackToAdd] = useState<Track | null>(null);
  const [globalSearch, setGlobalSearch] = useState(true); // Open by default
  const [isLoading, setIsLoading] = useState(false);
  const [foldersCollapsed, setFoldersCollapsed] = useState(true); // Collapsed by default
  
  // Search filters
  const [searchArtist, setSearchArtist] = useState('');
  const [searchTitle, setSearchTitle] = useState('');
  const [searchTags, setSearchTags] = useState('');
  const [searchDurationMin, setSearchDurationMin] = useState('');
  const [searchDurationMax, setSearchDurationMax] = useState('');
  
  const [newFolder, setNewFolder] = useState({
    name: '',
    path: '',
    recursive: false
  });

  useEffect(() => {
    loadMusicFolders();
    loadPlaylistFolder();
  }, []);

  useEffect(() => {
    if (selectedFolder) {
      loadTracks(selectedFolder);
    } else if (globalSearch) {
      loadAllTracks();
    }
  }, [selectedFolder, globalSearch, musicFolders]); // Add musicFolders dependency

  useEffect(() => {
    applyFilters();
  }, [tracks, searchArtist, searchTitle, searchTags, searchDurationMin, searchDurationMax]);

  useEffect(() => {
    if (playlistFolder) {
      loadAvailablePlaylists();
    }
  }, [playlistFolder]);

  const loadMusicFolders = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/audio/music`);
      const data = await response.json();
      setMusicFolders(data);
    } catch (err) {
      console.error('Error loading music folders:', err);
    }
  };

  const loadPlaylistFolder = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/audio/music/playlists-folder`);
      const data = await response.json();
      setPlaylistFolder(data.path || '');
    } catch (err) {
      console.error('Error loading playlist folder:', err);
    }
  };

  const loadAvailablePlaylists = async () => {
    try {
      // List playlists in the configured folder
      const response = await fetch(`${API_BASE_URL}/api/browse`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: playlistFolder })
      });
      const data = await response.json();
      const playlists = (data.items || [])
        .filter((item: any) => item.name.endsWith('.m3u'))
        .map((item: any) => ({
          name: item.name.replace('.m3u', ''),
          path: item.path
        }));
      setAvailablePlaylists(playlists);
    } catch (err) {
      console.error('Error loading available playlists:', err);
    }
  };

  const loadTracks = async (folderId: number) => {
    try {
      setIsLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/audio/music/${folderId}/tracks`);
      const data = await response.json();
      setTracks(data);
    } catch (err) {
      console.error('Error loading tracks:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const loadAllTracks = async () => {
    try {
      setIsLoading(true);
      // Load tracks from all folders concurrently
      const trackPromises = musicFolders.map(folder =>
        fetch(`${API_BASE_URL}/api/audio/music/${folder.id}/tracks`).then(res => res.json())
      );
      const allTracksArrays = await Promise.all(trackPromises);
      const allTracks = allTracksArrays.flat();
      setTracks(allTracks);
    } catch (err) {
      console.error('Error loading all tracks:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGlobalSearch = () => {
    setGlobalSearch(true);
    setSelectedFolder(null);
  };

  const refreshFolder = async (folderId: number) => {
    try {
      setIsLoading(true);
      await fetch(`${API_BASE_URL}/api/audio/music/${folderId}/refresh`, {
        method: 'POST'
      });
      // Reload tracks
      if (selectedFolder === folderId) {
        await loadTracks(folderId);
      } else if (globalSearch) {
        await loadAllTracks();
      }
    } catch (err) {
      console.error('Error refreshing folder:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const applyFilters = () => {
    let filtered = [...tracks];

    if (searchArtist) {
      const artistLower = searchArtist.toLowerCase();
      filtered = filtered.filter(t => 
        t.artist?.toLowerCase().includes(artistLower)
      );
    }

    if (searchTitle) {
      const titleLower = searchTitle.toLowerCase();
      filtered = filtered.filter(t => 
        (t.title || t.name).toLowerCase().includes(titleLower)
      );
    }

    if (searchTags) {
      const tagList = searchTags.split(',').map(t => t.trim().toLowerCase());
      filtered = filtered.filter(t => 
        t.tags?.some(tag => 
          tagList.some(searchTag => tag.toLowerCase().includes(searchTag))
        )
      );
    }

    if (searchDurationMin) {
      const minDuration = parseFloat(searchDurationMin);
      filtered = filtered.filter(t => (t.duration || 0) >= minDuration);
    }

    if (searchDurationMax) {
      const maxDuration = parseFloat(searchDurationMax);
      filtered = filtered.filter(t => (t.duration || 0) <= maxDuration);
    }

    setFilteredTracks(filtered);
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
      await fetch(`${API_BASE_URL}/api/audio/music`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newFolder)
      });
      setNewFolder({ name: '', path: '', recursive: false });
      setShowAddForm(false);
      loadMusicFolders();
    } catch (err) {
      console.error('Error adding music folder:', err);
    }
  };

  const handleUpdateFolder = async (folderId: number) => {
    try {
      await fetch(`${API_BASE_URL}/api/audio/music/${folderId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: editName })
      });
      setEditingFolder(null);
      setEditName('');
      loadMusicFolders();
    } catch (err) {
      console.error('Error updating music folder:', err);
    }
  };

  const handleDeleteFolder = async (folderId: number) => {
    if (!confirm('Are you sure you want to delete this music folder?')) {
      return;
    }
    try {
      await fetch(`${API_BASE_URL}/api/audio/music/${folderId}`, {
        method: 'DELETE'
      });
      if (selectedFolder === folderId) {
        setSelectedFolder(null);
        setTracks([]);
      }
      loadMusicFolders();
    } catch (err) {
      console.error('Error deleting music folder:', err);
    }
  };

  const handleSetPlaylistFolder = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await fetch(`${API_BASE_URL}/api/audio/music/playlists-folder`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: playlistFolder })
      });
      setShowPlaylistFolderForm(false);
      loadAvailablePlaylists();
      alert('Playlist folder configured successfully!');
    } catch (err) {
      console.error('Error setting playlist folder:', err);
      alert('Failed to set playlist folder');
    }
  };

  const toggleTrackSelection = (mediaId: string) => {
    const newSelection = new Set(selectedTracks);
    if (newSelection.has(mediaId)) {
      newSelection.delete(mediaId);
    } else {
      newSelection.add(mediaId);
    }
    setSelectedTracks(newSelection);
  };

  const toggleSelectAll = () => {
    const selectable = filteredTracks.filter(t => !!t.media_id);
    if (selectedTracks.size === selectable.length) {
      // Deselect all
      setSelectedTracks(new Set());
    } else {
      // Select all filtered tracks
      const allIds = new Set(selectable.map(t => t.media_id as string));
      setSelectedTracks(allIds);
    }
  };

  const handleAddToCurrentPlaylist = async () => {
    try {
      const mediaIds = Array.from(selectedTracks);
      
      const response = await fetch(`${API_BASE_URL}/api/audio/playback/add-tracks`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          media_ids: mediaIds
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        alert(`Added ${result.tracks_added} track(s) to current playlist. Total: ${result.total_tracks} tracks.`);
        setSelectedTracks(new Set()); // Clear selection
      } else {
        alert('Failed to add tracks to current playlist');
      }
    } catch (err) {
      console.error('Error adding tracks to current playlist:', err);
      alert('Error adding tracks to current playlist');
    }
  };

  const handleCreatePlaylist = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (selectedTracks.size === 0) {
      alert('Please select at least one track');
      return;
    }

    if (!playlistFolder) {
      alert('Please configure a playlist folder first');
      return;
    }

    try {
      const selectedTrackObjects = filteredTracks.filter(t => t.media_id && selectedTracks.has(t.media_id));
      const mediaIds = selectedTrackObjects.map(t => t.media_id).filter(Boolean);

      if (mediaIds.length === 0) {
        alert('Selected tracks are missing media_id');
        return;
      }

      const response = await fetch(`${API_BASE_URL}/api/audio/music/playlists/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          playlist_name: newPlaylistName,
          media_ids: mediaIds
        })
      });

      if (response.ok) {
        alert('Playlist created successfully!');
        setNewPlaylistName('');
        setShowCreatePlaylistForm(false);
        setSelectedTracks(new Set());
        loadAvailablePlaylists();
      } else {
        const error = await response.json();
        alert(`Failed to create playlist: ${error.error}`);
      }
    } catch (err) {
      console.error('Error creating playlist:', err);
      alert('Failed to create playlist');
    }
  };

  const handleAddToPlaylist = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedPlaylist || !trackToAdd) {
      return;
    }

    if (!trackToAdd.media_id) {
      alert('Selected track is missing media_id');
      return;
    }

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/audio/music/playlists/${selectedPlaylist}/add-track`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ media_id: trackToAdd.media_id })
        }
      );

      if (response.ok) {
        alert('Track added to playlist successfully!');
        setShowAddToPlaylistForm(false);
        setSelectedPlaylist('');
        setTrackToAdd(null);
      } else {
        const error = await response.json();
        alert(`Failed to add track: ${error.error}`);
      }
    } catch (err) {
      console.error('Error adding track to playlist:', err);
      alert('Failed to add track to playlist');
    }
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return '--:--';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="music-manager">
      <div className="music-header">
        <h2>Music Library</h2>
        <div className="music-actions">
          {currentUser?.role === 'admin' && (
            <>
              <button 
                onClick={() => setShowPlaylistFolderForm(true)}
                title="Configure Playlist Folder"
              >
                <span className="material-icons">folder_special</span>
              </button>
              <button 
                onClick={() => setShowAddForm(true)}
                title="Add Music Folder"
              >
                <span className="material-icons">add</span>
              </button>
            </>
          )}
          <button 
            onClick={handleGlobalSearch} 
            className="search-all-button"
            title="Search All Folders"
          >
            <span className="material-icons">search</span>
          </button>
          {selectedTracks.size > 0 && (
            <>
              {currentUser?.role === 'admin' && (
                <button 
                  onClick={() => setShowCreatePlaylistForm(true)}
                  title={`Create Playlist (${selectedTracks.size} tracks)`}
                >
                  <span className="material-icons">playlist_add</span>
                </button>
              )}
              <button 
                onClick={handleAddToCurrentPlaylist} 
                className="add-to-current-button"
                title={`Add to Current Playlist (${selectedTracks.size} tracks)`}
              >
                <span className="material-icons">queue_music</span>
              </button>
            </>
          )}
        </div>
      </div>

      {playlistFolder && (
        <div className="playlist-folder-info">
          <span className="material-icons">folder_special</span>
          Playlist Folder: {playlistFolder}
        </div>
      )}

      {showPlaylistFolderForm && (
        <div className="modal">
          <div className="modal-content">
            <h3>Configure Playlist Folder</h3>
            <form onSubmit={handleSetPlaylistFolder}>
              <div className="form-group">
                <label>Playlist Folder Path:</label>
                <div className="path-input-group">
                  <input
                    type="text"
                    value={playlistFolder}
                    onChange={(e) => setPlaylistFolder(e.target.value)}
                    required
                  />
                  <button
                    type="button"
                    onClick={() => browsePath_fn(playlistFolder || '/')}
                    title="Browse folders"
                  >
                    <span className="material-icons">folder_open</span>
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
                              setPlaylistFolder(item.path);
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
                      setPlaylistFolder(browsePath);
                      setBrowseItems([]);
                    }}
                    title="Select current folder"
                  >
                    <span className="material-icons">check</span>
                  </button>
                </div>
              )}

              <div className="form-actions">
                <button type="submit" title="Save playlist folder">
                  <span className="material-icons">check</span>
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowPlaylistFolderForm(false);
                    setBrowseItems([]);
                  }}
                  title="Cancel"
                >
                  <span className="material-icons">close</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showAddForm && (
        <div className="modal">
          <div className="modal-content">
            <h3>Add Music Folder</h3>
            <form onSubmit={handleAddFolder}>
              <div className="form-group">
                <label>Folder Name:</label>
                <input
                  type="text"
                  value={newFolder.name}
                  onChange={(e) => setNewFolder({ ...newFolder, name: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label>Folder Path:</label>
                <div className="path-input-group">
                  <input
                    type="text"
                    value={newFolder.path}
                    onChange={(e) => setNewFolder({ ...newFolder, path: e.target.value })}
                    required
                  />
                  <button
                    type="button"
                    onClick={() => browsePath_fn(newFolder.path || '/')}
                    title="Browse folders"
                  >
                    <span className="material-icons">folder_open</span>
                  </button>
                </div>
              </div>

              <div className="form-group">
                <label>
                  <input
                    type="checkbox"
                    checked={newFolder.recursive}
                    onChange={(e) => setNewFolder({ ...newFolder, recursive: e.target.checked })}
                  />
                  Scan subfolders recursively
                </label>
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
                    title="Select current folder"
                  >
                    <span className="material-icons">check</span>
                  </button>
                </div>
              )}

              <div className="form-actions">
                <button type="submit" title="Add music folder">
                  <span className="material-icons">add</span>
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowAddForm(false);
                    setBrowseItems([]);
                  }}
                  title="Cancel"
                >
                  <span className="material-icons">close</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showCreatePlaylistForm && (
        <div className="modal">
          <div className="modal-content">
            <h3>Create New Playlist</h3>
            <form onSubmit={handleCreatePlaylist}>
              <div className="form-group">
                <label>Playlist Name:</label>
                <input
                  type="text"
                  value={newPlaylistName}
                  onChange={(e) => setNewPlaylistName(e.target.value)}
                  required
                />
              </div>
              <p>{selectedTracks.size} track(s) selected</p>
              <div className="form-actions">
                <button type="submit" title="Create playlist">
                  <span className="material-icons">playlist_add</span>
                </button>
                <button
                  type="button"
                  onClick={() => setShowCreatePlaylistForm(false)}
                  title="Cancel"
                >
                  <span className="material-icons">close</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showAddToPlaylistForm && (
        <div className="modal">
          <div className="modal-content">
            <h3>Add Track to Playlist</h3>
            <form onSubmit={handleAddToPlaylist}>
              <div className="form-group">
                <label>Select Playlist:</label>
                <select
                  value={selectedPlaylist}
                  onChange={(e) => setSelectedPlaylist(e.target.value)}
                  required
                >
                  <option value="">-- Select Playlist --</option>
                  {availablePlaylists.map((pl) => (
                    <option key={pl.name} value={pl.name}>
                      {pl.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-actions">
                <button type="submit" title="Add to playlist">
                  <span className="material-icons">playlist_add</span>
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowAddToPlaylistForm(false);
                    setSelectedPlaylist('');
                    setTrackToAdd(null);
                  }}
                  title="Cancel"
                >
                  <span className="material-icons">close</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="music-folders">
        <h3 onClick={() => setFoldersCollapsed(!foldersCollapsed)}>
          <span className="material-icons">
            {foldersCollapsed ? 'expand_more' : 'expand_less'}
          </span>
          Music Folders
        </h3>
        {!foldersCollapsed && (
          <>
            {musicFolders.length === 0 ? (
              <p className="empty-message">No music folders configured</p>
            ) : (
              <ul>
                {musicFolders.map((folder) => (
                  <li
                    key={folder.id}
                    className={selectedFolder === folder.id ? 'selected' : ''}
                  >
                    {editingFolder === folder.id ? (
                      <div className="editing">
                        <input
                          type="text"
                          value={editName}
                          onChange={(e) => setEditName(e.target.value)}
                          onKeyPress={(e) => {
                            if (e.key === 'Enter') {
                              handleUpdateFolder(folder.id);
                            }
                          }}
                        />
                        <button onClick={() => handleUpdateFolder(folder.id)}>
                          <span className="material-icons">check</span>
                        </button>
                        <button onClick={() => setEditingFolder(null)}>
                          <span className="material-icons">close</span>
                        </button>
                      </div>
                    ) : (
                      <>
                        <div
                          className="folder-info"
                          onClick={() => {
                            setSelectedFolder(folder.id);
                            setGlobalSearch(false);
                          }}
                        >
                          <span className="material-icons">
                            {folder.recursive ? 'folder_open' : 'folder'}
                          </span>
                          <div>
                            <div className="folder-name">{folder.name}</div>
                            <div className="folder-path">{folder.path}</div>
                            {folder.recursive && (
                              <div className="folder-badge">Recursive</div>
                            )}
                          </div>
                        </div>
                        <div className="folder-actions">
                          <button
                            onClick={() => refreshFolder(folder.id)}
                            title="Refresh folder"
                          >
                            <span className="material-icons">refresh</span>
                          </button>
                          {currentUser?.role === 'admin' && (
                            <>
                              <button
                                onClick={() => {
                                  setEditingFolder(folder.id);
                                  setEditName(folder.name);
                                }}
                              >
                                <span className="material-icons">edit</span>
                              </button>
                              <button onClick={() => handleDeleteFolder(folder.id)}>
                                <span className="material-icons">delete</span>
                              </button>
                            </>
                          )}
                        </div>
                      </>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </>
        )}
      </div>

      {(selectedFolder || globalSearch) && (
        <div className="music-tracks">
          <h3>{globalSearch ? 'All Tracks' : 'Tracks'}</h3>
          
          <div className="search-filters">
            <h4>Search Filters</h4>
            <div className="filter-row">
              <input
                type="text"
                placeholder="Artist"
                value={searchArtist}
                onChange={(e) => setSearchArtist(e.target.value)}
              />
              <input
                type="text"
                placeholder="Title"
                value={searchTitle}
                onChange={(e) => setSearchTitle(e.target.value)}
              />
              <input
                type="text"
                placeholder="Tags (comma-separated)"
                value={searchTags}
                onChange={(e) => setSearchTags(e.target.value)}
              />
            </div>
            <div className="filter-row">
              <input
                type="number"
                placeholder="Min Duration (seconds)"
                value={searchDurationMin}
                onChange={(e) => setSearchDurationMin(e.target.value)}
              />
              <input
                type="number"
                placeholder="Max Duration (seconds)"
                value={searchDurationMax}
                onChange={(e) => setSearchDurationMax(e.target.value)}
              />
                <button
                  onClick={() => {
                    setSearchArtist('');
                    setSearchTitle('');
                    setSearchTags('');
                    setSearchDurationMin('');
                    setSearchDurationMax('');
                  }}
                  title="Clear all filters"
                >
                  <span className="material-icons">clear</span>
                </button>
            </div>
          </div>

          {isLoading ? (
            <div className="loading-container">
              <div className="loading-spinner"></div>
              <p>Loading tracks...</p>
            </div>
          ) : filteredTracks.length === 0 ? (
            <p className="empty-message">
              {tracks.length === 0 
                ? 'No tracks found'
                : 'No tracks match your search criteria'}
            </p>
          ) : (
            <div className="tracks-list">
              <div className="tracks-header">
                <div>
                  <label>
                    <input
                      type="checkbox"
                      checked={
                        filteredTracks.some(t => !!t.media_id) &&
                        filteredTracks.filter(t => !!t.media_id).every(t => selectedTracks.has(t.media_id as string))
                      }
                      onChange={toggleSelectAll}
                    />
                    <span className="select-all-text">
                      Select All ({filteredTracks.filter(t => !!t.media_id).length} track(s))
                    </span>
                  </label>
                </div>
              </div>
              <table>
                <thead>
                  <tr>
                    <th></th>
                    <th>Title</th>
                    <th>Artist</th>
                    <th>Album</th>
                    <th>Duration</th>
                    <th>Tags</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredTracks.map((track, idx) => (
                    <tr key={idx}>
                      <td>
                        <input
                          type="checkbox"
                          checked={!!track.media_id && selectedTracks.has(track.media_id)}
                          onChange={() => track.media_id && toggleTrackSelection(track.media_id)}
                          disabled={!track.media_id}
                        />
                      </td>
                      <td data-label="Title">{track.title || track.name}</td>
                      <td data-label="Artist">{track.artist || '-'}</td>
                      <td data-label="Album">{track.album || '-'}</td>
                      <td data-label="Duration">{formatDuration(track.duration)}</td>
                      <td data-label="Tags">
                        {track.tags && track.tags.length > 0 ? (
                          <div className="tags">
                            {track.tags.map((tag, i) => (
                              <span key={i} className="tag">{tag}</span>
                            ))}
                          </div>
                        ) : '-'}
                      </td>
                      <td data-label="Actions">
                        <button
                          onClick={() => {
                            setTrackToAdd(track);
                            setShowAddToPlaylistForm(true);
                          }}
                          disabled={!track.media_id || !playlistFolder || availablePlaylists.length === 0}
                          title={
                            !track.media_id
                              ? 'Track is missing media id'
                              : !playlistFolder 
                              ? 'Configure playlist folder first'
                              : availablePlaylists.length === 0
                                ? 'Create a playlist first'
                                : 'Add to playlist'
                          }
                        >
                          <span className="material-icons">playlist_add</span>
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default MusicManager;
