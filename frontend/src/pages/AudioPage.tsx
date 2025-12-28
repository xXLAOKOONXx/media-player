import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import PlaylistManager from '../components/PlaylistManager';
import PlaybackControls from '../components/PlaybackControls';
import NowPlaying from '../components/NowPlaying';
import SoundEffectsManager from '../components/SoundEffectsManager';
import MusicManager from '../components/MusicManager';

// Use relative URL - works for both dev (proxied) and production (same origin)
const API_BASE_URL = '';

function AudioPage() {
  const navigate = useNavigate();
  const location = useLocation();
  
  // Derive active tab from URL path
  const getActiveTabFromPath = () => {
    const path = location.pathname;
    if (path.includes('/player')) return 'player';
    if (path.includes('/playlists')) return 'playlists';
    if (path.includes('/music')) return 'music';
    if (path.includes('/soundeffects')) return 'soundeffects';
    return 'player'; // default
  };

  const [activeTab, setActiveTab] = useState<'playlists' | 'player' | 'soundeffects' | 'music'>(getActiveTabFromPath());
  const [playbackStatus, setPlaybackStatus] = useState<any>(null);

  // Sync activeTab with URL changes
  useEffect(() => {
    setActiveTab(getActiveTabFromPath());
  }, [location.pathname]);

  // Update URL when tab changes
  const handleTabChange = (tab: typeof activeTab) => {
    setActiveTab(tab);
    navigate(`/audio/${tab}`);
  };

  useEffect(() => {
    // Poll playback status
    const interval = setInterval(() => {
      fetch(`${API_BASE_URL}/api/audio/playback/status`)
        .then(res => res.json())
        .then(data => setPlaybackStatus(data))
        .catch(err => console.error('Error fetching status:', err));
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="audio-page">
      <nav className="tabs">
        <button 
          className={activeTab === 'player' ? 'active' : ''} 
          onClick={() => handleTabChange('player')}
        >
          Player
        </button>
        <button 
          className={activeTab === 'playlists' ? 'active' : ''} 
          onClick={() => handleTabChange('playlists')}
        >
          Playlists
        </button>
        <button 
          className={activeTab === 'music' ? 'active' : ''} 
          onClick={() => handleTabChange('music')}
        >
          Music
        </button>
        <button 
          className={activeTab === 'soundeffects' ? 'active' : ''} 
          onClick={() => handleTabChange('soundeffects')}
        >
          Sound Effects
        </button>
      </nav>

      <main className="App-main">
        {activeTab === 'player' && (
          <div className="player-view">
            <NowPlaying status={playbackStatus} />
            <PlaybackControls status={playbackStatus} onUpdate={() => {}} />
          </div>
        )}
        
        {activeTab === 'playlists' && (
          <PlaylistManager />
        )}
        
        {activeTab === 'music' && (
          <MusicManager />
        )}
        
        {activeTab === 'soundeffects' && (
          <SoundEffectsManager />
        )}
      </main>
    </div>
  );
}

export default AudioPage;
