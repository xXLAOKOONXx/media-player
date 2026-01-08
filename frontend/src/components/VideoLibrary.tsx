import { useState, useEffect } from 'react';
import type { User } from '../types';
import { createWeightedPlaylist } from '../utils/playlistUtils';
import './VideoLibrary.css';
import VideoDetailsModal from './VideoDetailsModal';

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
  media_id?: string;
  size: number;
  director?: string;
  artist?: string;
  title?: string;
  series?: string;
  duration?: number;
  start_time_in_ms?: number;
  end_time_in_ms?: number;
  tags?: string[];
  description?: string;
  user_rating?: number;
  playcount?: number;
  last_played?: number | null;
  promotion_score?: number;
  modified?: number;
}

const truncateText = (value: string, maxChars: number) => {
  if (value.length <= maxChars) return value;
  return `${value.slice(0, maxChars)}…`;
};

const getArtistText = (video: Video) => {
  // Prefer enhanced metadata field; fall back to legacy `director`.
  const artist = (video.artist || '').trim();
  if (artist) return artist;
  const director = (video.director || '').trim();
  return director;
};

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
  const [playlistOrderMode, setPlaylistOrderMode] = useState<'current' | 'shuffle'>('current');
  const [playlistOccurrenceMode, setPlaylistOccurrenceMode] = useState<'once' | 'rating' | 'rating_squared'>('once');
  const [availablePlaylists, setAvailablePlaylists] = useState<Playlist[]>([]);
  const [showAddToPlaylistForm, setShowAddToPlaylistForm] = useState(false);
  const [selectedPlaylist, setSelectedPlaylist] = useState('');
  const [videoToAdd, setVideoToAdd] = useState<Video | null>(null);
  const [showBulkAddToPlaylistForm, setShowBulkAddToPlaylistForm] = useState(false);
  const [bulkSelectedPlaylist, setBulkSelectedPlaylist] = useState('');
  const [detailsVideo, setDetailsVideo] = useState<Video | null>(null);

  const applyUserMetadataUpdate = (updated: {
    media_id?: string;
    user_rating?: number | null;
    tags?: string[];
    start_time_in_ms?: number | null;
    end_time_in_ms?: number | null;
  }) => {
    if (!updated.media_id) return;
    setVideos((prev) =>
      prev.map((v) =>
        v.media_id === updated.media_id
          ? {
              ...v,
              user_rating: updated.user_rating == null ? undefined : updated.user_rating,
              tags: updated.tags,
              start_time_in_ms: updated.start_time_in_ms == null ? undefined : updated.start_time_in_ms,
              end_time_in_ms: updated.end_time_in_ms == null ? undefined : updated.end_time_in_ms,
            }
          : v,
      ),
    );
    setDetailsVideo((prev) =>
      prev && prev.media_id === updated.media_id
        ? {
            ...prev,
            user_rating: updated.user_rating == null ? undefined : updated.user_rating,
            tags: updated.tags,
            start_time_in_ms: updated.start_time_in_ms == null ? undefined : updated.start_time_in_ms,
            end_time_in_ms: updated.end_time_in_ms == null ? undefined : updated.end_time_in_ms,
          }
        : prev,
    );
  };
  const [globalSearch, setGlobalSearch] = useState(true); // Open by default
  const [isLoading, setIsLoading] = useState(false);
  const [foldersCollapsed, setFoldersCollapsed] = useState(true); // Collapsed by default
  
  // Search filters
  const [searchArtist, setSearchArtist] = useState('');
  const [searchTitle, setSearchTitle] = useState('');
  const [searchTags, setSearchTags] = useState<string[]>([]);
  const [searchDurationMin, setSearchDurationMin] = useState('');
  const [searchDurationMax, setSearchDurationMax] = useState('');
  const [searchPlaycountMin, setSearchPlaycountMin] = useState('');
  const [searchPlaycountMax, setSearchPlaycountMax] = useState('');
  const [searchRatingMin, setSearchRatingMin] = useState('');
  const [searchRatingMax, setSearchRatingMax] = useState('');
  const [searchPromotionScoreMin, setSearchPromotionScoreMin] = useState('');
  const [searchPromotionScoreMax, setSearchPromotionScoreMax] = useState('');
  
  // Configurable columns
  const [visibleColumns, setVisibleColumns] = useState({
    title: true,
    artist: true,
    album: true,
    duration: true,
    tags: true,
    playcount: false,
    lastPlayed: false,
    promotionScore: false,
    userRating: false,
    modified: false,
  });
  const [showColumnConfig, setShowColumnConfig] = useState(false);
  
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
  }, [videos, searchArtist, searchTitle, searchTags, searchDurationMin, searchDurationMax, 
      searchPlaycountMin, searchPlaycountMax, searchRatingMin, searchRatingMax,
      searchPromotionScoreMin, searchPromotionScoreMax]);

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
      // List playlists in the configured folder (safe endpoint; not a generic filesystem browser)
      const response = await fetch(`${API_BASE_URL}/api/video/playlists-folder/files`);
      if (!response.ok) {
        setAvailablePlaylists([]);
        return;
      }
      const data = await response.json();
      setAvailablePlaylists(Array.isArray(data) ? data : []);
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
      const artistLower = searchArtist.toLowerCase();
      filtered = filtered.filter(t =>
        getArtistText(t).toLowerCase().includes(artistLower)
      );
    }

    if (searchTitle) {
      const titleLower = searchTitle.toLowerCase();
      filtered = filtered.filter(t => 
        (t.title || t.name).toLowerCase().includes(titleLower)
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

    // Tags filter - support array of selected tags and "No Tags" option
    if (searchTags.length > 0) {
      filtered = filtered.filter(t => {
        // Check if "No Tags" is selected
        if (searchTags.includes('__NO_TAGS__')) {
          return !t.tags || t.tags.length === 0;
        }
        
        // All selected tags must match (AND logic)
        return searchTags.every(searchTag => 
          t.tags?.some(tag => tag.toLowerCase() === searchTag.toLowerCase())
        );
      });
    }

    // Playcount filters
    if (searchPlaycountMin) {
      const minPlaycount = parseInt(searchPlaycountMin);
      filtered = filtered.filter(t => (t.playcount || 0) >= minPlaycount);
    }
    if (searchPlaycountMax) {
      const maxPlaycount = parseInt(searchPlaycountMax);
      filtered = filtered.filter(t => (t.playcount || 0) <= maxPlaycount);
    }

    // User rating filters
    if (searchRatingMin) {
      const minRating = parseFloat(searchRatingMin);
      filtered = filtered.filter(t => (t.user_rating || 0) >= minRating);
    }
    if (searchRatingMax) {
      const maxRating = parseFloat(searchRatingMax);
      filtered = filtered.filter(t => (t.user_rating || 0) <= maxRating);
    }

    // Promotion score filters
    if (searchPromotionScoreMin) {
      const minScore = parseFloat(searchPromotionScoreMin);
      filtered = filtered.filter(t => (t.promotion_score || 0) >= minScore);
    }
    if (searchPromotionScoreMax) {
      const maxScore = parseFloat(searchPromotionScoreMax);
      filtered = filtered.filter(t => (t.promotion_score || 0) <= maxScore);
    }

    setFilteredVideos(filtered);
  };

  // Get all unique tags from videos
  const getAllUniqueTags = (): string[] => {
    const tagsSet = new Set<string>();
    videos.forEach(video => {
      video.tags?.forEach(tag => tagsSet.add(tag));
    });
    return Array.from(tagsSet).sort();
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return '--:--';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatTimestamp = (timestamp?: number | null) => {
    if (!timestamp) return '-';
    const date = new Date(timestamp * 1000);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
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

  const toggleVideoSelection = (mediaId: string) => {
    const newSelection = new Set(selectedVideos);
    if (newSelection.has(mediaId)) {
      newSelection.delete(mediaId);
    } else {
      newSelection.add(mediaId);
    }
    setSelectedVideos(newSelection);
  };

  const toggleSelectAll = () => {
    const selectable = filteredVideos.filter(t => !!t.media_id);
    if (selectedVideos.size === selectable.length) {
      // Deselect all
      setSelectedVideos(new Set());
    } else {
      // Select all filtered videos
      const allIds = new Set(selectable.map(t => t.media_id as string));
      setSelectedVideos(allIds);
    }
  };

  const getSelectedMediaIdsInOrder = () => {
    const ordered: string[] = [];
    for (const v of filteredVideos) {
      if (v.media_id && selectedVideos.has(v.media_id)) {
        ordered.push(v.media_id);
      }
    }
    return ordered;
  };

  const handleAddToCurrentPlaylist = async () => {
    try {
      const mediaIds = getSelectedMediaIdsInOrder();
      
      const response = await fetch(`${API_BASE_URL}/api/video/playback/add-videos`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          media_ids: mediaIds
        })
      });
      
      if (response.ok) {
        alert(`Added ${mediaIds.length} video(s) to current playlist.`);
        setSelectedVideos(new Set()); // Clear selection
      } else {
        alert('Failed to add videos to current playlist');
      }
    } catch (err) {
      console.error('Error adding videos to current playlist:', err);
      alert('Error adding videos to current playlist');
    }
  };

  const handleAddSingleToCurrentPlaylist = async (video: Video) => {
    if (!video.media_id) {
      alert('Selected video is missing media_id');
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/video/playback/add-videos`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          media_ids: [video.media_id]
        })
      });

      if (response.ok) {
        alert('Added video to current playlist.');
      } else {
        alert('Failed to add video to current playlist');
      }
    } catch (err) {
      console.error('Error adding video to current playlist:', err);
      alert('Error adding video to current playlist');
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
      const selectedVideoObjects = filteredVideos.filter(t => t.media_id && selectedVideos.has(t.media_id));

      if (selectedVideoObjects.length === 0) {
        alert('Selected videos are missing media_id');
        return;
      }

      // Apply weighted playlist logic
      const mediaIds = createWeightedPlaylist(
        selectedVideoObjects,
        playlistOccurrenceMode,
        playlistOrderMode
      );

      if (mediaIds.length === 0) {
        alert('No videos to add to playlist (check ratings if using rating-based occurrence)');
        return;
      }

      const response = await fetch(`${API_BASE_URL}/api/video/playlists/create`, {
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
        setSelectedVideos(new Set());
        setPlaylistOrderMode('current');
        setPlaylistOccurrenceMode('once');
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

    if (!videoToAdd.media_id) {
      alert('Selected video is missing media_id');
      return;
    }

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/video/playlists/${selectedPlaylist}/add-video`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ media_id: videoToAdd.media_id })
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

  const handleBulkAddToPlaylist = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!bulkSelectedPlaylist) {
      return;
    }
    if (selectedVideos.size === 0) {
      alert('Please select at least one video');
      return;
    }

    const mediaIds = getSelectedMediaIdsInOrder();
    if (mediaIds.length === 0) {
      alert('Selected videos are missing media_id');
      return;
    }

    try {
      for (const media_id of mediaIds) {
        // Use existing endpoint; add in display order.
        const res = await fetch(`${API_BASE_URL}/api/video/playlists/${bulkSelectedPlaylist}/add-video`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ media_id })
        });
        if (!res.ok) {
          const error = await res.json().catch(() => null);
          alert(`Failed to add one or more videos: ${error?.error || 'Request failed'}`);
          return;
        }
      }

      alert('Videos added to playlist successfully!');
      setShowBulkAddToPlaylistForm(false);
      setBulkSelectedPlaylist('');
      setSelectedVideos(new Set());
    } catch (err) {
      console.error('Error adding videos to playlist:', err);
      alert('Failed to add videos to playlist');
    }
  };

  const startPlayback = async (video: { media_id?: string }) => {
    try {
      if (!video.media_id) {
        alert('Missing media_id for selected video');
        return;
      }
      const res = await fetch(`${API_BASE_URL}/api/video/playback/play-video`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ media_id: video.media_id })
      });

      if (!res.ok) {
        const data = await res.json().catch(() => null);
        const msg = data?.error || 'Failed to start playback';
        alert(msg);
        return;
      }
    } catch (err) {
      console.error('Error starting playback:', err);
      alert('Failed to start playback');
    }
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
              {!!currentUser && (
                <button onClick={() => setShowCreatePlaylistForm(true)}>
                  <span className="material-icons">playlist_add</span>
                  Create Playlist ({selectedVideos.size})
                </button>
              )}
              {!!currentUser && (
                <button
                  onClick={() => setShowBulkAddToPlaylistForm(true)}
                  disabled={!playlistFolder || availablePlaylists.length === 0}
                  title={
                    !playlistFolder
                      ? 'Configure playlist folder first'
                      : availablePlaylists.length === 0
                        ? 'Create a playlist first'
                        : 'Add selected videos to an existing playlist'
                  }
                >
                  <span className="material-icons">playlist_add</span>
                  Add to Playlist ({selectedVideos.size})
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
              
              <div className="form-group">
                <label>Order:</label>
                <select 
                  value={playlistOrderMode} 
                  onChange={(e) => setPlaylistOrderMode(e.target.value as 'current' | 'shuffle')}
                >
                  <option value="current">Current Order</option>
                  <option value="shuffle">Shuffle</option>
                </select>
              </div>

              <div className="form-group">
                <label>Occurrence:</label>
                <select 
                  value={playlistOccurrenceMode} 
                  onChange={(e) => setPlaylistOccurrenceMode(e.target.value as 'once' | 'rating' | 'rating_squared')}
                >
                  <option value="once">Everything Once</option>
                  <option value="rating">Amount = Rating</option>
                  <option value="rating_squared">Amount = Rating²</option>
                </select>
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

      {showBulkAddToPlaylistForm && (
        <div className="modal">
          <div className="modal-content">
            <h3>Add Selected Videos to Playlist</h3>
            <form onSubmit={handleBulkAddToPlaylist}>
              <div className="form-group">
                <label>Select Playlist:</label>
                <select
                  value={bulkSelectedPlaylist}
                  onChange={(e) => setBulkSelectedPlaylist(e.target.value)}
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
              <p>{selectedVideos.size} video(s) selected</p>
              <div className="form-actions">
                <button type="submit">Add to Playlist</button>
                <button
                  type="button"
                  onClick={() => {
                    setShowBulkAddToPlaylistForm(false);
                    setBulkSelectedPlaylist('');
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
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
              <h4>Search Filters</h4>
              <button onClick={() => setShowColumnConfig(!showColumnConfig)}>
                <span className="material-icons">view_column</span>
                Configure Columns
              </button>
            </div>

            {showColumnConfig && (
              <div className="column-config" style={{ 
                backgroundColor: 'var(--card-background)', 
                padding: '15px', 
                marginBottom: '15px',
                borderRadius: '8px',
                border: '1px solid var(--border-color)'
              }}>
                <h5>Visible Columns</h5>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))', gap: '10px' }}>
                  <label>
                    <input
                      type="checkbox"
                      checked={visibleColumns.title}
                      onChange={(e) => setVisibleColumns({ ...visibleColumns, title: e.target.checked })}
                    />
                    Title
                  </label>
                  <label>
                    <input
                      type="checkbox"
                      checked={visibleColumns.artist}
                      onChange={(e) => setVisibleColumns({ ...visibleColumns, artist: e.target.checked })}
                    />
                    Artist
                  </label>
                  <label>
                    <input
                      type="checkbox"
                      checked={visibleColumns.album}
                      onChange={(e) => setVisibleColumns({ ...visibleColumns, album: e.target.checked })}
                    />
                    Album
                  </label>
                  <label>
                    <input
                      type="checkbox"
                      checked={visibleColumns.duration}
                      onChange={(e) => setVisibleColumns({ ...visibleColumns, duration: e.target.checked })}
                    />
                    Duration
                  </label>
                  <label>
                    <input
                      type="checkbox"
                      checked={visibleColumns.tags}
                      onChange={(e) => setVisibleColumns({ ...visibleColumns, tags: e.target.checked })}
                    />
                    Tags
                  </label>
                  <label>
                    <input
                      type="checkbox"
                      checked={visibleColumns.playcount}
                      onChange={(e) => setVisibleColumns({ ...visibleColumns, playcount: e.target.checked })}
                    />
                    Play Count
                  </label>
                  <label>
                    <input
                      type="checkbox"
                      checked={visibleColumns.lastPlayed}
                      onChange={(e) => setVisibleColumns({ ...visibleColumns, lastPlayed: e.target.checked })}
                    />
                    Last Played
                  </label>
                  <label>
                    <input
                      type="checkbox"
                      checked={visibleColumns.promotionScore}
                      onChange={(e) => setVisibleColumns({ ...visibleColumns, promotionScore: e.target.checked })}
                    />
                    Promotion Score
                  </label>
                  <label>
                    <input
                      type="checkbox"
                      checked={visibleColumns.userRating}
                      onChange={(e) => setVisibleColumns({ ...visibleColumns, userRating: e.target.checked })}
                    />
                    User Rating
                  </label>
                  <label>
                    <input
                      type="checkbox"
                      checked={visibleColumns.modified}
                      onChange={(e) => setVisibleColumns({ ...visibleColumns, modified: e.target.checked })}
                    />
                    Modified
                  </label>
                </div>
              </div>
            )}

            <div className="filter-row">
              {visibleColumns.artist && (
                <input
                  type="text"
                  placeholder="Artist"
                  value={searchArtist}
                  onChange={(e) => setSearchArtist(e.target.value)}
                />
              )}
              {visibleColumns.title && (
                <input
                  type="text"
                  placeholder="Title"
                  value={searchTitle}
                  onChange={(e) => setSearchTitle(e.target.value)}
                />
              )}
              {visibleColumns.tags && (
                <div style={{ flex: 1 }}>
                  <select
                    multiple
                    value={searchTags}
                    onChange={(e) => {
                      const options = Array.from(e.target.selectedOptions, option => option.value);
                      setSearchTags(options);
                    }}
                    style={{ width: '100%', minHeight: '38px' }}
                  >
                    <option value="__NO_TAGS__">No Tags</option>
                    {getAllUniqueTags().map(tag => (
                      <option key={tag} value={tag}>{tag}</option>
                    ))}
                  </select>
                  {searchTags.length > 0 && (
                    <div style={{ fontSize: '12px', marginTop: '2px' }}>
                      Selected: {searchTags.map(t => t === '__NO_TAGS__' ? 'No Tags' : t).join(', ')}
                    </div>
                  )}
                </div>
              )}
            </div>
            
            <div className="filter-row">
              {visibleColumns.duration && (
                <>
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
                </>
              )}
              {visibleColumns.playcount && (
                <>
                  <input
                    type="number"
                    placeholder="Min Play Count"
                    value={searchPlaycountMin}
                    onChange={(e) => setSearchPlaycountMin(e.target.value)}
                  />
                  <input
                    type="number"
                    placeholder="Max Play Count"
                    value={searchPlaycountMax}
                    onChange={(e) => setSearchPlaycountMax(e.target.value)}
                  />
                </>
              )}
              {visibleColumns.userRating && (
                <>
                  <input
                    type="number"
                    placeholder="Min Rating (0-10)"
                    value={searchRatingMin}
                    onChange={(e) => setSearchRatingMin(e.target.value)}
                    min="0"
                    max="10"
                    step="0.1"
                  />
                  <input
                    type="number"
                    placeholder="Max Rating (0-10)"
                    value={searchRatingMax}
                    onChange={(e) => setSearchRatingMax(e.target.value)}
                    min="0"
                    max="10"
                    step="0.1"
                  />
                </>
              )}
              {visibleColumns.promotionScore && (
                <>
                  <input
                    type="number"
                    placeholder="Min Promotion Score"
                    value={searchPromotionScoreMin}
                    onChange={(e) => setSearchPromotionScoreMin(e.target.value)}
                    step="0.1"
                  />
                  <input
                    type="number"
                    placeholder="Max Promotion Score"
                    value={searchPromotionScoreMax}
                    onChange={(e) => setSearchPromotionScoreMax(e.target.value)}
                    step="0.1"
                  />
                </>
              )}
            </div>

            <div className="filter-row">
              <button
                onClick={() => {
                  setSearchArtist('');
                  setSearchTitle('');
                  setSearchTags([]);
                  setSearchDurationMin('');
                  setSearchDurationMax('');
                  setSearchPlaycountMin('');
                  setSearchPlaycountMax('');
                  setSearchRatingMin('');
                  setSearchRatingMax('');
                  setSearchPromotionScoreMin('');
                  setSearchPromotionScoreMax('');
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
                      checked={
                        selectedVideos.size === filteredVideos.filter(t => !!t.media_id).length &&
                        filteredVideos.filter(t => !!t.media_id).length > 0
                      }
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
                    {visibleColumns.title && <th>Title</th>}
                    {visibleColumns.artist && <th>Artist</th>}
                    {visibleColumns.album && <th>Album</th>}
                    {visibleColumns.duration && <th>Duration</th>}
                    {visibleColumns.tags && <th>Tags</th>}
                    {visibleColumns.playcount && <th>Play Count</th>}
                    {visibleColumns.lastPlayed && <th>Last Played</th>}
                    {visibleColumns.promotionScore && <th>Promotion Score</th>}
                    {visibleColumns.userRating && <th>User Rating</th>}
                    {visibleColumns.modified && <th>Modified</th>}
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredVideos.map((track, idx) => (
                    <tr
                      key={idx}
                      className="video-library-row"
                      onClick={() => setDetailsVideo(track)}
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault();
                          setDetailsVideo(track);
                        }
                      }}
                    >
                      <td>
                        <input
                          type="checkbox"
                          checked={!!track.media_id && selectedVideos.has(track.media_id)}
                          disabled={!track.media_id}
                          onChange={() => track.media_id && toggleVideoSelection(track.media_id)}
                          onClick={(e) => e.stopPropagation()}
                        />
                      </td>
                      {visibleColumns.title && <td data-label="Title">{track.title || track.name}</td>}
                      {visibleColumns.artist && (
                        <td data-label="Artist" title={getArtistText(track) || undefined}>
                          {getArtistText(track)
                            ? truncateText(getArtistText(track), 30)
                            : '-'}
                        </td>
                      )}
                      {visibleColumns.album && <td data-label="Album">{track.series || '-'}</td>}
                      {visibleColumns.duration && <td data-label="Duration">{formatDuration(track.duration)}</td>}
                      {visibleColumns.tags && (
                        <td data-label="Tags">
                          {track.tags && track.tags.length > 0 ? (
                            <div className="tags">
                              {track.tags.map((tag, i) => (
                                <span key={i} className="tag">{tag}</span>
                              ))}
                            </div>
                          ) : '-'}
                        </td>
                      )}
                      {visibleColumns.playcount && (
                        <td data-label="Play Count">{track.playcount || 0}</td>
                      )}
                      {visibleColumns.lastPlayed && (
                        <td data-label="Last Played">{formatTimestamp(track.last_played)}</td>
                      )}
                      {visibleColumns.promotionScore && (
                        <td data-label="Promotion Score">
                          {track.promotion_score !== undefined ? track.promotion_score.toFixed(2) : '-'}
                        </td>
                      )}
                      {visibleColumns.userRating && (
                        <td data-label="User Rating">
                          {track.user_rating !== undefined ? track.user_rating.toFixed(1) : '-'}
                        </td>
                      )}
                      {visibleColumns.modified && (
                        <td data-label="Modified">{formatTimestamp(track.modified)}</td>
                      )}
                      <td data-label="Actions">
                        <button
                          onClick={() => {
                            setDetailsVideo(null);
                            setVideoToAdd(track);
                            setShowAddToPlaylistForm(true);
                          }}
                          onMouseDown={(e) => e.stopPropagation()}
                          onClickCapture={(e) => e.stopPropagation()}
                          disabled={!currentUser || !playlistFolder || availablePlaylists.length === 0}
                          title={
                            !currentUser
                              ? 'Login required'
                              : !playlistFolder 
                                ? 'Configure playlist folder first'
                                : availablePlaylists.length === 0
                                  ? 'Create a playlist first'
                                  : 'Add to playlist'
                          }
                        >
                          <span className="material-icons">playlist_add</span>
                        </button>

                        <button
                          onClick={() => handleAddSingleToCurrentPlaylist(track)}
                          onMouseDown={(e) => e.stopPropagation()}
                          onClickCapture={(e) => e.stopPropagation()}
                          disabled={!track.media_id}
                          title={!track.media_id ? 'Missing media_id' : 'Add to current playlist'}
                        >
                          <span className="material-icons">queue_music</span>
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {detailsVideo && (
            <VideoDetailsModal
              video={detailsVideo}
              onClose={() => setDetailsVideo(null)}
              onPlay={(video) => startPlayback(video)}
              onVideoUpdated={(updatedVideo) => applyUserMetadataUpdate(updatedVideo)}
            />
          )}
        </div>
      )}
    </div>
  );
};

export default VideoLibrary;
