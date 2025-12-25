import { useState, useEffect } from 'react';
import './VideoPage.css';

const API_BASE_URL = '';

interface VideoFolder {
  id: number;
  name: string;
  path: string;
  recursive: boolean;
}

interface Video {
  name: string;
  path: string;
  size: number;
  title?: string;
  duration?: number;
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

interface AudioTrack {
  index: number;
  description?: string;
}

interface SubtitleTrack {
  index: number;
  description?: string;
}

interface PlaybackStatus {
  state: string;
  current_index?: number;
  playlist_length?: number;
  volume?: number;
  audio_tracks?: AudioTrack[];
  subtitle_tracks?: SubtitleTrack[];
  current_audio_track?: number;
  current_subtitle_track?: number;
  current_track?: {
    path: string;
    name: string;
    title: string;
  };
  position?: number;
  time?: number;
  length?: number;
}

function VideoPage() {
  const [activeTab, setActiveTab] = useState<'player' | 'library' | 'playlists'>('library');
  const [playbackStatus, setPlaybackStatus] = useState<PlaybackStatus | null>(null);
  const [videoFolders, setVideoFolders] = useState<VideoFolder[]>([]);
  const [videos, setVideos] = useState<Video[]>([]);
  const [filteredVideos, setFilteredVideos] = useState<Video[]>([]);
  const [selectedFolder, setSelectedFolder] = useState<number | null>(null);
  const [playlists, setPlaylists] = useState<Playlist[]>([]);
  const [audioTracks, setAudioTracks] = useState<AudioTrack[]>([]);
  const [subtitleTracks, setSubtitleTracks] = useState<SubtitleTrack[]>([]);
  const [selectedAudioTrack, setSelectedAudioTrack] = useState<number>(0);
  const [selectedSubtitleTrack, setSelectedSubtitleTrack] = useState<number>(-1);
  const [showAddFolderForm, setShowAddFolderForm] = useState(false);
  const [showPlaylistFolderForm, setShowPlaylistFolderForm] = useState(false);
  const [showCreatePlaylistForm, setShowCreatePlaylistForm] = useState(false);
  const [browsePath, setBrowsePath] = useState('/');
  const [browseItems, setBrowseItems] = useState<BrowseItem[]>([]);
  const [editingFolder, setEditingFolder] = useState<number | null>(null);
  const [editName, setEditName] = useState('');
  const [playlistFolder, setPlaylistFolder] = useState('');
  const [newPlaylistName, setNewPlaylistName] = useState('');
  const [selectedVideos, setSelectedVideos] = useState<Set<string>>(new Set());
  const [foldersCollapsed, setFoldersCollapsed] = useState(true);
  const [searchTitle, setSearchTitle] = useState('');
  const [newFolder, setNewFolder] = useState({
    name: '',
    path: '',
    recursive: false
  });

  useEffect(() => {
    // Poll playback status
    const interval = setInterval(() => {
      fetch(`${API_BASE_URL}/api/video/playback/status`)
        .then(res => res.json())
        .then(data => {
          setPlaybackStatus(data);
          if (data.audio_tracks) setAudioTracks(data.audio_tracks);
          if (data.subtitle_tracks) setSubtitleTracks(data.subtitle_tracks);
        })
        .catch(err => console.error('Error fetching status:', err));
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    loadVideoFolders();
    loadPlaylists();
    loadPlaylistFolder();
  }, []);

  useEffect(() => {
    if (selectedFolder) {
      loadVideos(selectedFolder);
    }
  }, [selectedFolder]);

  useEffect(() => {
    applyFilters();
  }, [videos, searchTitle]);

  useEffect(() => {
    if (playlistFolder) {
      loadPlaylists();
    }
  }, [playlistFolder]);

  const loadVideoFolders = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/video/folders`);
      const data = await response.json();
      setVideoFolders(data);
    } catch (err) {
      console.error('Error loading video folders:', err);
    }
  };

  const loadVideos = async (folderId: number) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/video/folders/${folderId}/videos`);
      const data = await response.json();
      setVideos(data);
    } catch (err) {
      console.error('Error loading videos:', err);
    }
  };

  const loadPlaylists = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/video/playlists`);
      const data = await response.json();
      setPlaylists(data);
    } catch (err) {
      console.error('Error loading playlists:', err);
    }
  };

  const playVideo = async (videoPath: string) => {
    try {
      await fetch(`${API_BASE_URL}/api/video/playback/play`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ video_path: videoPath })
      });
    } catch (err) {
      console.error('Error playing video:', err);
    }
  };

  const playPlaylist = async (playlistPath: string) => {
    try {
      await fetch(`${API_BASE_URL}/api/video/playback/play`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ playlist_path: playlistPath })
      });
    } catch (err) {
      console.error('Error playing playlist:', err);
    }
  };

  const handlePause = async () => {
    try {
      await fetch(`${API_BASE_URL}/api/video/playback/pause`, { method: 'POST' });
    } catch (err) {
      console.error('Error pausing video:', err);
    }
  };

  const handleStop = async () => {
    try {
      await fetch(`${API_BASE_URL}/api/video/playback/stop`, { method: 'POST' });
    } catch (err) {
      console.error('Error stopping video:', err);
    }
  };

  const handleNext = async () => {
    try {
      await fetch(`${API_BASE_URL}/api/video/playback/next`, { method: 'POST' });
    } catch (err) {
      console.error('Error going to next video:', err);
    }
  };

  const handlePrevious = async () => {
    try {
      await fetch(`${API_BASE_URL}/api/video/playback/previous`, { method: 'POST' });
    } catch (err) {
      console.error('Error going to previous video:', err);
    }
  };

  const handleAudioTrackChange = async (trackIndex: number) => {
    try {
      await fetch(`${API_BASE_URL}/api/video/playback/audio-track`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ track_index: trackIndex })
      });
      setSelectedAudioTrack(trackIndex);
    } catch (err) {
      console.error('Error changing audio track:', err);
    }
  };

  const handleSubtitleTrackChange = async (trackIndex: number) => {
    try {
      await fetch(`${API_BASE_URL}/api/video/playback/subtitle-track`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ track_index: trackIndex })
      });
      setSelectedSubtitleTrack(trackIndex);
    } catch (err) {
      console.error('Error changing subtitle track:', err);
    }
  };

  const loadPlaylistFolder = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/video/playlists/folder`);
      if (response.ok) {
        const data = await response.json();
        setPlaylistFolder(data.path || '');
      }
    } catch (err) {
      console.error('Error loading playlist folder:', err);
    }
  };

  const handleSetPlaylistFolder = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await fetch(`${API_BASE_URL}/api/video/playlists/folder`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: playlistFolder })
      });
      if (response.ok) {
        setShowPlaylistFolderForm(false);
        setBrowseItems([]);
        loadPlaylists();
      }
    } catch (err) {
      console.error('Error setting playlist folder:', err);
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
      setBrowsePath(data.current_path || path);
      setBrowseItems(data.items || []);
    } catch (err) {
      console.error('Error browsing path:', err);
    }
  };

  const applyFilters = () => {
    let filtered = videos;
    if (searchTitle) {
      const titleLower = searchTitle.toLowerCase();
      filtered = filtered.filter(v => 
        (v.title || v.name).toLowerCase().includes(titleLower)
      );
    }
    setFilteredVideos(filtered);
  };

  const toggleVideoSelection = (videoPath: string) => {
    const newSelected = new Set(selectedVideos);
    if (newSelected.has(videoPath)) {
      newSelected.delete(videoPath);
    } else {
      newSelected.add(videoPath);
    }
    setSelectedVideos(newSelected);
  };

  const toggleSelectAll = () => {
    if (selectedVideos.size === filteredVideos.length && filteredVideos.length > 0) {
      setSelectedVideos(new Set());
    } else {
      setSelectedVideos(new Set(filteredVideos.map(v => v.path)));
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
      const selectedVideoObjects = filteredVideos.filter(v => 
        selectedVideos.has(v.path)
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
        loadPlaylists();
      } else {
        const error = await response.json();
        alert(`Failed to create playlist: ${error.error}`);
      }
    } catch (err) {
      console.error('Error creating playlist:', err);
      alert('Failed to create playlist');
    }
  };

  const handleUpdateFolder = async (folderId: number) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/video/folders/${folderId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: editName })
      });
      if (response.ok) {
        setEditingFolder(null);
        loadVideoFolders();
      }
    } catch (err) {
      console.error('Error updating folder:', err);
    }
  };

  const handleDeleteFolder = async (folderId: number) => {
    if (!confirm('Are you sure you want to delete this folder?')) return;
    try {
      const response = await fetch(`${API_BASE_URL}/api/video/folders/${folderId}`, {
        method: 'DELETE'
      });
      if (response.ok) {
        if (selectedFolder === folderId) {
          setSelectedFolder(null);
          setVideos([]);
        }
        loadVideoFolders();
      }
    } catch (err) {
      console.error('Error deleting folder:', err);
    }
  };

  const refreshFolder = async (folderId: number) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/video/folders/${folderId}/refresh`, {
        method: 'POST'
      });
      if (response.ok) {
        if (selectedFolder === folderId) {
          loadVideos(folderId);
        }
      }
    } catch (err) {
      console.error('Error refreshing folder:', err);
    }
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return '--:--';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleAddToCurrentPlaylist = async () => {
    if (selectedVideos.size === 0) {
      alert('Please select at least one video');
      return;
    }

    try {
      const selectedVideoPaths = Array.from(selectedVideos);
      const response = await fetch(`${API_BASE_URL}/api/video/playback/add-tracks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ track_paths: selectedVideoPaths })
      });

      if (response.ok) {
        const result = await response.json();
        alert(`Added ${result.tracks_added} video(s) to current playlist`);
        setSelectedVideos(new Set());
      } else {
        alert('Failed to add videos to current playlist');
      }
    } catch (err) {
      console.error('Error adding videos to current playlist:', err);
      alert('Error adding videos to current playlist');
    }
  };

  const handleAddFolder = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!newFolder.name || !newFolder.path) {
      alert('Please provide both folder name and path');
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/video/folders`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newFolder)
      });

      if (response.ok) {
        setShowAddFolderForm(false);
        setNewFolder({ name: '', path: '', recursive: false });
        loadVideoFolders();
      } else {
        alert('Failed to add video folder');
      }
    } catch (err) {
      console.error('Error adding video folder:', err);
      alert('Error adding video folder');
    }
  };

  return (
    <div className="video-page">
      <nav className="tabs">
        <button 
          className={activeTab === 'player' ? 'active' : ''} 
          onClick={() => setActiveTab('player')}
        >
          Player
        </button>
        <button 
          className={activeTab === 'playlists' ? 'active' : ''} 
          onClick={() => setActiveTab('playlists')}
        >
          Playlists
        </button>
        <button 
          className={activeTab === 'library' ? 'active' : ''} 
          onClick={() => setActiveTab('library')}
        >
          Video Library
        </button>
      </nav>

      <main className="page-content">
        {activeTab === 'player' && (
          <div className="player-view">
            <div className="now-playing">
              <h2>Now Playing</h2>
              {playbackStatus?.current_track ? (
                <div className="track-info">
                  <h3>{playbackStatus.current_track.title || playbackStatus.current_track.name}</h3>
                  <p>Status: {playbackStatus.state}</p>
                </div>
              ) : (
                <p>No video playing</p>
              )}
            </div>

            <div className="playback-controls">
              <button onClick={handlePrevious}>
                <span className="material-icons">skip_previous</span>
              </button>
              <button onClick={handlePause}>
                <span className="material-icons">
                  {playbackStatus?.state === 'playing' ? 'pause' : 'play_arrow'}
                </span>
              </button>
              <button onClick={handleStop}>
                <span className="material-icons">stop</span>
              </button>
              <button onClick={handleNext}>
                <span className="material-icons">skip_next</span>
              </button>
            </div>

            <div className="track-selection">
              <div className="audio-tracks">
                <h3>Audio Track</h3>
                <select 
                  value={selectedAudioTrack} 
                  onChange={(e) => handleAudioTrackChange(Number(e.target.value))}
                >
                  {audioTracks.map((track) => (
                    <option key={track.index} value={track.index}>
                      {track.description || `Track ${track.index + 1}`}
                    </option>
                  ))}
                </select>
              </div>

              <div className="subtitle-tracks">
                <h3>Subtitles</h3>
                <select 
                  value={selectedSubtitleTrack} 
                  onChange={(e) => handleSubtitleTrackChange(Number(e.target.value))}
                >
                  <option value={-1}>None</option>
                  {subtitleTracks.map((track) => (
                    <option key={track.index} value={track.index}>
                      {track.description || `Track ${track.index + 1}`}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'playlists' && (
          <div className="playlists-view">
            <div className="playlist-header">
              <h2>Video Playlists</h2>
              <button onClick={() => setShowPlaylistFolderForm(true)}>
                <span className="material-icons">folder</span>
                Configure Playlist Folder
              </button>
            </div>

            {playlistFolder && (
              <div className="playlist-folder-info">
                <span className="material-icons">folder_special</span>
                Playlist Folder: {playlistFolder}
              </div>
            )}

            {playlists.length === 0 ? (
              <div className="empty-state">
                <span className="material-icons" style={{ fontSize: '48px' }}>playlist_play</span>
                <p>No video playlists found</p>
                <p>{playlistFolder ? 'Add .m3u playlist files to your configured folder' : 'Configure a playlist folder to get started'}</p>
              </div>
            ) : (
              <div className="playlist-list">
                {playlists.map((playlist, index) => (
                  <div key={index} className="playlist-item">
                    <span className="material-icons">movie</span>
                    <span className="playlist-name">{playlist.name}</span>
                    <button onClick={() => playPlaylist(playlist.path)}>
                      <span className="material-icons">play_arrow</span>
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'library' && (
          <div className="library-view">
            <div className="library-header">
              <h2>Video Library</h2>
              <div className="library-actions">
                <button onClick={() => setShowPlaylistFolderForm(true)}>
                  <span className="material-icons">folder</span>
                  Configure Playlist Folder
                </button>
                <button onClick={() => setShowAddFolderForm(true)}>
                  <span className="material-icons">add</span>
                  Add Video Folder
                </button>
                {selectedVideos.size > 0 && (
                  <>
                    <button onClick={() => setShowCreatePlaylistForm(true)}>
                      <span className="material-icons">playlist_add</span>
                      Create Playlist ({selectedVideos.size})
                    </button>
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
            
            <div className="video-folders">
              <h3 onClick={() => setFoldersCollapsed(!foldersCollapsed)}>
                <span className="material-icons">
                  {foldersCollapsed ? 'expand_more' : 'expand_less'}
                </span>
                Video Folders
              </h3>
              {!foldersCollapsed && (
                <>
                  {videoFolders.length === 0 ? (
                    <p className="empty-message">No video folders configured</p>
                  ) : (
                    <ul>
                      {videoFolders.map((folder) => (
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
                                onClick={() => setSelectedFolder(folder.id)}
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

            {selectedFolder && (
              <div className="video-tracks">
                <h3>Videos</h3>
                
                <div className="search-filters">
                  <h4>Search Filters</h4>
                  <div className="filter-row">
                    <input
                      type="text"
                      placeholder="Title"
                      value={searchTitle}
                      onChange={(e) => setSearchTitle(e.target.value)}
                    />
                    <button onClick={() => setSearchTitle('')}>
                      Clear Filters
                    </button>
                  </div>
                </div>

                {filteredVideos.length === 0 ? (
                  <p className="empty-message">
                    {videos.length === 0 
                      ? 'No videos found in this folder'
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
                          <th>Duration</th>
                          <th>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {filteredVideos.map((video, idx) => (
                          <tr key={idx}>
                            <td>
                              <input
                                type="checkbox"
                                checked={selectedVideos.has(video.path)}
                                onChange={() => toggleVideoSelection(video.path)}
                              />
                            </td>
                            <td data-label="Title">{video.title || video.name}</td>
                            <td data-label="Duration">{formatDuration(video.duration)}</td>
                            <td data-label="Actions">
                              <button
                                onClick={() => playVideo(video.path)}
                                title="Play video"
                              >
                                <span className="material-icons">play_arrow</span>
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
        )}
      </main>

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

      {showCreatePlaylistForm && (
        <div className="modal">
          <div className="modal-content">
            <h3>Create Video Playlist</h3>
            <form onSubmit={handleCreatePlaylist}>
              <div className="form-group">
                <label>Playlist Name:</label>
                <input
                  type="text"
                  value={newPlaylistName}
                  onChange={(e) => setNewPlaylistName(e.target.value)}
                  placeholder="My Playlist"
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

      {showAddFolderForm && (
        <div className="modal">
          <div className="modal-content">
            <h3>Add Video Folder</h3>
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
                    placeholder="/path/to/videos"
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
                      setNewFolder({ ...newFolder, path: browsePath });
                      setBrowseItems([]);
                    }}
                  >
                    Select Current Folder
                  </button>
                </div>
              )}

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

              <div className="form-actions">
                <button type="submit">Add Folder</button>
                <button
                  type="button"
                  onClick={() => {
                    setShowAddFolderForm(false);
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
    </div>
  );
}

export default VideoPage;
