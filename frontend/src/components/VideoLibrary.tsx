import { useState, useEffect } from 'react';
import type { User } from '../types';
import './VideoLibrary.css';

const API_BASE_URL = '';

interface VideoLibrary {
  id: number;
  name: string;
  path: string;
  recursive: boolean;
  storage_id?: number;
}

interface Video {
  name: string;
  path: string;
  size: number;
  director?: string;
  title?: string;
  series?: string;
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

interface VideoLibraryProps {
  currentUser?: User;
}

const VideoLibrary = ({ currentUser }: VideoLibraryProps) => {
  const [videoLibraries, setVideoLibraries] = useState<VideoLibrary[]>([]);
  const [videos, setVideos] = useState<Video[]>([]);
  const [filteredVideos, setFilteredVideos] = useState<Video[]>([]);
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
  const [selectedVideos, setSelectedVideos] = useState<Set<string>>(new Set());
  const [availablePlaylists, setAvailablePlaylists] = useState<Playlist[]>([]);
  const [showAddToPlaylistForm, setShowAddToPlaylistForm] = useState(false);
  const [selectedPlaylist, setSelectedPlaylist] = useState('');
  const [videoToAdd, setVideoToAdd] = useState<Video | null>(null);
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
    loadVideoLibraries();
    loadPlaylistFolder();
  }, []);

  useEffect(() => {
    if (selectedFolder) {
      loadVideos(selectedFolder);
    } else if (globalSearch) {
      loadAllVideos();
    }
  }, [selectedFolder, globalSearch, videoLibraries]); // Add videoLibraries dependency

  useEffect(() => {
    applyFilters();
  }, [videos, searchArtist, searchTitle, searchTags, searchDurationMin, searchDurationMax]);

  useEffect(() => {
    if (playlistFolder) {
      loadAvailablePlaylists();
    }
  }, [playlistFolder]);

  const loadVideoLibraries = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/video/libraries`);
      const data = await response.json();
      setVideoLibraries(data);
    } catch (err) {
      console.error('Error loading video libraries:', err);
    }
  };

  const loadPlaylistFolder = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/video/playlists-folder`);
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

  const loadVideos = async (folderId: number) => {
    try {
      setIsLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/video/libraries/${folderId}/videos`);
      const data = await response.json();
      setVideos(data);
    } catch (err) {
      console.error('Error loading videos:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const loadAllVideos = async () => {
    try {
      setIsLoading(true);
      // Load videos from all folders concurrently
      const trackPromises = videoLibraries.map(folder =>
        fetch(`${API_BASE_URL}/api/video/libraries/${folder.id}/videos`).then(res => res.json())
      );
      const allVideosArrays = await Promise.all(trackPromises);
      const allVideos = allVideosArrays.flat();
      setVideos(allVideos);
    } catch (err) {
      console.error('Error loading all videos:', err);
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
      await fetch(`${API_BASE_URL}/api/video/libraries/${folderId}/refresh`, {
        method: 'POST'
      });
      // Reload videos
      if (selectedFolder === folderId) {
        await loadVideos(folderId);
      } else if (globalSearch) {
        await loadAllVideos();
      }
    } catch (err) {
      console.error('Error refreshing folder:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const applyFilters = () => {
    let filtered = [...videos];

    if (searchArtist) {
      const directorLower = searchArtist.toLowerCase();
      filtered = filtered.filter(t => 
        t.director?.toLowerCase().includes(directorLower)
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

    setFilteredVideos(filtered);
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
      await fetch(`${API_BASE_URL}/api/video/libraries`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newFolder)
      });
      setNewFolder({ name: '', path: '', recursive: false });
      setShowAddForm(false);
      loadVideoLibraries();
    } catch (err) {
      console.error('Error adding video library:', err);
    }
  };

  const handleUpdateFolder = async (folderId: number) => {
    try {
      await fetch(`${API_BASE_URL}/api/video/libraries/${folderId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: editName })
      });
      setEditingFolder(null);
      setEditName('');
      loadVideoLibraries();
    } catch (err) {
      console.error('Error updating video library:', err);
    }
  };

  const handleDeleteFolder = async (folderId: number) => {
    if (!confirm('Are you sure you want to delete this video library?')) {
      return;
    }
    try {
      await fetch(`${API_BASE_URL}/api/video/libraries/${folderId}`, {
        method: 'DELETE'
      });
      if (selectedFolder === folderId) {
        setSelectedFolder(null);
        setVideos([]);
      }
      loadVideoLibraries();
    } catch (err) {
      console.error('Error deleting video library:', err);
    }
  };

  const handleSetPlaylistFolder = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await fetch(`${API_BASE_URL}/api/video/playlists-folder`, {
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

  const toggleVideoSelection = (trackPath: string) => {
    const newSelection = new Set(selectedVideos);
    if (newSelection.has(trackPath)) {
      newSelection.delete(trackPath);
    } else {
      newSelection.add(trackPath);
    }
    setSelectedVideos(newSelection);
  };

  const toggleSelectAll = () => {
    if (selectedVideos.size === filteredVideos.length) {
      // Deselect all
      setSelectedVideos(new Set());
    } else {
      // Select all filtered videos
      const allPaths = new Set(filteredVideos.map(t => t.path));
      setSelectedVideos(allPaths);
    }
  };

  const handleAddToCurrentPlaylist = async () => {
    try {
      const videoPaths = Array.from(selectedVideos);
      
      const response = await fetch(`${API_BASE_URL}/api/video/playback/add-videos`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          video_paths: videoPaths
        })
      });
      
      if (response.ok) {
        alert(`Added ${videoPaths.length} video(s) to current playlist.`);
        setSelectedVideos(new Set()); // Clear selection
      } else {
        alert('Failed to add videos to current playlist');
      }
    } catch (err) {
      console.error('Error adding videos to current playlist:', err);
      alert('Error adding videos to current playlist');
    }
  };

  const handleCreatePlaylist = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (selectedVideos.size === 0) {
      alert('Please select at least one video');
      return;
    }

    if (!playlistFolder) {
      alert('Please configure a playlist folder first');
      return;
    }

    try {
      const selectedVideoObjects = filteredVideos.filter(t => 
        selectedVideos.has(t.path)
      );

      const response = await fetch(`${API_BASE_URL}/api/video/playlists/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          playlist_name: newPlaylistName,
          videos: selectedVideoObjects
        })
      });

      if (response.ok) {
        alert('Playlist created successfully!');
        setNewPlaylistName('');
        setShowCreatePlaylistForm(false);
        setSelectedVideos(new Set());
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
    
    if (!selectedPlaylist || !videoToAdd) {
      return;
    }

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/video/playlists/${selectedPlaylist}/add-video`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ video: videoToAdd })
        }
      );

      if (response.ok) {
        alert('Video added to playlist successfully!');
        setShowAddToPlaylistForm(false);
        setSelectedPlaylist('');
        setVideoToAdd(null);
      } else {
        const error = await response.json();
        alert(`Failed to add video: ${error.error}`);
      }
    } catch (err) {
      console.error('Error adding video to playlist:', err);
      alert('Failed to add video to playlist');
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
        <h2>Video Library</h2>
        <div className="music-actions">
          {currentUser?.role === 'admin' && (
            <>
              <button onClick={() => setShowPlaylistFolderForm(true)}>
                <span className="material-icons">folder</span>
                Configure Playlist Folder
              </button>
              <button onClick={() => setShowAddForm(true)}>
                <span className="material-icons">add</span>
                Add Video Library
              </button>
            </>
          )}
          <button onClick={handleGlobalSearch} className="search-all-button">
            <span className="material-icons">search</span>
            Search All Folders
          </button>
          {selectedVideos.size > 0 && (
            <>
              {currentUser?.role === 'admin' && (
                <button onClick={() => setShowCreatePlaylistForm(true)}>
                  <span className="material-icons">playlist_add</span>
                  Create Playlist ({selectedVideos.size})
                </button>
              )}
              <button onClick={handleAddToCurrentPlaylist} className="add-to-current-button">
                <span className="material-icons">queue_music</span>
                Add to Current Playlist ({selectedVideos.size})
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
                  >
                    Select Current Folder
                  </button>
                </div>
              )}

              <div className="form-actions">
                <button type="submit">Save</button>
                <button
                  type="button"
                  onClick={() => {
                    setShowPlaylistFolderForm(false);
                    setBrowseItems([]);
                  }}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showAddForm && (
        <div className="modal">
          <div className="modal-content">
            <h3>Add Video Library</h3>
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
                  >
                    Browse
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
                  >
                    Select Current Folder
                  </button>
                </div>
              )}

              <div className="form-actions">
                <button type="submit">Add Folder</button>
                <button
                  type="button"
                  onClick={() => {
                    setShowAddForm(false);
                    setBrowseItems([]);
                  }}
                >
                  Cancel
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
              <p>{selectedVideos.size} video(s) selected</p>
              <div className="form-actions">
                <button type="submit">Create Playlist</button>
                <button
                  type="button"
                  onClick={() => setShowCreatePlaylistForm(false)}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showAddToPlaylistForm && (
        <div className="modal">
          <div className="modal-content">
            <h3>Add Video to Playlist</h3>
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
                <button type="submit">Add to Playlist</button>
                <button
                  type="button"
                  onClick={() => {
                    setShowAddToPlaylistForm(false);
                    setSelectedPlaylist('');
                    setVideoToAdd(null);
                  }}
                >
                  Cancel
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
          Video Libraries
        </h3>
        {!foldersCollapsed && (
          <>
            {videoLibraries.length === 0 ? (
              <p className="empty-message">No video libraries configured</p>
            ) : (
              <ul>
                {videoLibraries.map((folder) => (
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
        <div className="music-videos">
          <h3>{globalSearch ? 'All Videos' : 'Videos'}</h3>
          
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
              >
                Clear Filters
              </button>
            </div>
          </div>

          {isLoading ? (
            <div className="loading-container">
              <div className="loading-spinner"></div>
              <p>Loading videos...</p>
            </div>
          ) : filteredVideos.length === 0 ? (
            <p className="empty-message">
              {videos.length === 0 
                ? 'No videos found'
                : 'No videos match your search criteria'}
            </p>
          ) : (
            <div className="videos-list">
              <div className="videos-header">
                <div>
                  <label>
                    <input
                      type="checkbox"
                      checked={selectedVideos.size === filteredVideos.length && filteredVideos.length > 0}
                      onChange={toggleSelectAll}
                    />
                    <span className="select-all-text">Select All ({filteredVideos.length} video(s))</span>
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
                  {filteredVideos.map((track, idx) => (
                    <tr key={idx}>
                      <td>
                        <input
                          type="checkbox"
                          checked={selectedVideos.has(track.path)}
                          onChange={() => toggleVideoSelection(track.path)}
                        />
                      </td>
                      <td data-label="Title">{track.title || track.name}</td>
                      <td data-label="Artist">{track.director || '-'}</td>
                      <td data-label="Album">{track.series || '-'}</td>
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
                            setVideoToAdd(track);
                            setShowAddToPlaylistForm(true);
                          }}
                          disabled={!playlistFolder || availablePlaylists.length === 0}
                          title={
                            !playlistFolder 
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

export default VideoLibrary;
