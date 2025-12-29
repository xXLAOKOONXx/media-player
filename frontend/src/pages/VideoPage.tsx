import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import type { User } from '../types';
import './VideoPage.css';
import VideoLibrary from '../components/VideoLibrary';
import VideoPlaylistManager from '../components/VideoPlaylistManager';
import VideoPlayer from '../components/VideoPlayer';
import VideoPlaybackControls from '../components/VideoPlaybackControls';
import SettingsManager from '../components/SettingsManager';
import VideoExplorer from '../components/VideoExplorer';

// Use relative URL - works for both dev (proxied) and production (same origin)
const API_BASE_URL = '';

interface VideoPageProps {
  currentUser: User;
}

function VideoPage({ currentUser }: VideoPageProps) {
  const navigate = useNavigate();
  const location = useLocation();
  
  // Derive active tab from URL path
  const getActiveTabFromPath = () => {
    const path = location.pathname;
    if (path.includes('/explorer')) return 'explorer';
    if (path.includes('/player')) return 'player';
    if (path.includes('/playlists')) return 'playlists';
    if (path.includes('/library')) return 'library';
    if (path.includes('/settings')) return 'settings';
    return 'player'; // default
  };

  const [activeTab, setActiveTab] = useState<'library' | 'playlists' | 'player' | 'settings' | 'explorer'>(getActiveTabFromPath());
  const [playbackStatus, setPlaybackStatus] = useState<any>(null);

  // Sync activeTab with URL changes
  useEffect(() => {
    setActiveTab(getActiveTabFromPath());
  }, [location.pathname]);

  // Update URL when tab changes
  const handleTabChange = (tab: typeof activeTab) => {
    setActiveTab(tab);
    navigate(`/video/${tab}`);
  };

  useEffect(() => {
    // Poll playback status
    const interval = setInterval(() => {
      fetch(`${API_BASE_URL}/api/video/playback/status`)
        .then(res => res.json())
        .then(data => setPlaybackStatus(data))
        .catch(err => console.error('Error fetching status:', err));
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="video-page">
      <nav className="tabs">
        <button 
          className={activeTab === 'player' ? 'active' : ''} 
          onClick={() => handleTabChange('player')}
        >
          Player
        </button>
        <button 
          className={activeTab === 'explorer' ? 'active' : ''} 
          onClick={() => handleTabChange('explorer')}
        >
          Explorer
        </button>
        <button 
          className={activeTab === 'playlists' ? 'active' : ''} 
          onClick={() => handleTabChange('playlists')}
        >
          Playlists
        </button>
        <button 
          className={activeTab === 'library' ? 'active' : ''} 
          onClick={() => handleTabChange('library')}
        >
          Library
        </button>
        <button 
          className={activeTab === 'settings' ? 'active' : ''} 
          onClick={() => handleTabChange('settings')}
        >
          Settings
        </button>
      </nav>

      <main className="video-main">
        {activeTab === 'player' && (
          <div className="player-view">
            <VideoPlayer status={playbackStatus} />
            <VideoPlaybackControls status={playbackStatus} onUpdate={() => {}} />
          </div>
        )}

        {activeTab === 'explorer' && (
          <VideoExplorer />
        )}
        
        {activeTab === 'playlists' && (
          <VideoPlaylistManager currentUser={currentUser} />
        )}
        
        {activeTab === 'library' && (
          <VideoLibrary currentUser={currentUser} />
        )}
        
        {activeTab === 'settings' && (
          <SettingsManager currentUser={currentUser} />
        )}
      </main>
    </div>
  );
}

export default VideoPage;
