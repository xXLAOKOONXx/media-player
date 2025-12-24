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
  const [activeTab, setActiveTab] = useState<'player' | 'library' | 'playlists'>('player');
  const [playbackStatus, setPlaybackStatus] = useState<PlaybackStatus | null>(null);
  const [videoFolders, setVideoFolders] = useState<VideoFolder[]>([]);
  const [videos, setVideos] = useState<Video[]>([]);
  const [selectedFolder, setSelectedFolder] = useState<number | null>(null);
  const [playlists, setPlaylists] = useState<Playlist[]>([]);
  const [audioTracks, setAudioTracks] = useState<AudioTrack[]>([]);
  const [subtitleTracks, setSubtitleTracks] = useState<SubtitleTrack[]>([]);
  const [selectedAudioTrack, setSelectedAudioTrack] = useState<number>(0);
  const [selectedSubtitleTrack, setSelectedSubtitleTrack] = useState<number>(-1);
  const [showAddFolderForm, setShowAddFolderForm] = useState(false);
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
  }, []);

  useEffect(() => {
    if (selectedFolder) {
      loadVideos(selectedFolder);
    }
  }, [selectedFolder]);

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
            <h2>Video Playlists</h2>
            {playlists.length === 0 ? (
              <div className="empty-state">
                <span className="material-icons" style={{ fontSize: '48px' }}>playlist_play</span>
                <p>No video playlists found</p>
                <p>Configure a video playlist folder in the settings or add .m3u playlist files to your configured folder</p>
              </div>
            ) : (
              <div className="playlist-list">
                {playlists.map((playlist, index) => (
                  <div key={index} className="playlist-item">
                    <span>{playlist.name}</span>
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
              <button className="btn btn-primary" onClick={() => setShowAddFolderForm(true)}>
                <span className="material-icons">add</span>
                Add Video Folder
              </button>
            </div>
            
            {videoFolders.length === 0 ? (
              <div className="empty-state">
                <span className="material-icons" style={{ fontSize: '48px' }}>video_library</span>
                <p>No video folders configured</p>
                <p>Click "Add Video Folder" to get started</p>
              </div>
            ) : (
              <>
                <div className="folders-section">
                  <h3>Folders</h3>
                  <div className="folder-list">
                    {videoFolders.map((folder) => (
                      <button
                        key={folder.id}
                        className={selectedFolder === folder.id ? 'active' : ''}
                        onClick={() => setSelectedFolder(folder.id)}
                      >
                        {folder.name}
                      </button>
                    ))}
                  </div>
                </div>

                {selectedFolder && (
                  <div className="videos-section">
                    <h3>Videos</h3>
                    {videos.length === 0 ? (
                      <div className="empty-state">
                        <span className="material-icons" style={{ fontSize: '36px' }}>movie</span>
                        <p>No videos found in this folder</p>
                      </div>
                    ) : (
                      <div className="video-list">
                        {videos.map((video, index) => (
                          <div key={index} className="video-item">
                            <div className="video-info">
                              <h4>{video.title || video.name}</h4>
                              {video.duration && <span>{Math.floor(video.duration / 60)}:{String(Math.floor(video.duration % 60)).padStart(2, '0')}</span>}
                            </div>
                            <button onClick={() => playVideo(video.path)}>
                              <span className="material-icons">play_arrow</span>
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </main>

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
                <input
                  type="text"
                  value={newFolder.path}
                  onChange={(e) => setNewFolder({ ...newFolder, path: e.target.value })}
                  placeholder="/path/to/videos"
                  required
                />
              </div>

              <div className="form-group">
                <label>
                  <input
                    type="checkbox"
                    checked={newFolder.recursive}
                    onChange={(e) => setNewFolder({ ...newFolder, recursive: e.target.checked })}
                  />
                  Scan subdirectories recursively
                </label>
              </div>

              <div className="modal-actions">
                <button type="submit" className="btn btn-primary">Add Folder</button>
                <button type="button" className="btn btn-secondary" onClick={() => setShowAddFolderForm(false)}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default VideoPage;
