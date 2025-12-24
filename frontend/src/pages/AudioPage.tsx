import { useState, useEffect } from 'react';
import StorageManager from '../components/StorageManager';
import PlaylistManager from '../components/PlaylistManager';
import PlaybackControls from '../components/PlaybackControls';
import NowPlaying from '../components/NowPlaying';
import TrackTimesEditor from '../components/TrackTimesEditor';
import SoundEffectsManager from '../components/SoundEffectsManager';
import MusicManager from '../components/MusicManager';
import './AudioPage.css';

const API_BASE_URL = '';

function AudioPage() {
  const [activeTab, setActiveTab] = useState<'storage' | 'playlists' | 'player' | 'tracks' | 'soundeffects' | 'music'>('player');
  const [playbackStatus, setPlaybackStatus] = useState<any>(null);

  useEffect(() => {
    // Poll playback status
    const interval = setInterval(() => {
      fetch(`${API_BASE_URL}/api/playback/status`)
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
          onClick={() => setActiveTab('player')}
        >
          Player
        </button>
        <button 
          className={activeTab === 'tracks' ? 'active' : ''} 
          onClick={() => setActiveTab('tracks')}
        >
          Track Times
        </button>
        <button 
          className={activeTab === 'playlists' ? 'active' : ''} 
          onClick={() => setActiveTab('playlists')}
        >
          Playlists
        </button>
        <button 
          className={activeTab === 'music' ? 'active' : ''} 
          onClick={() => setActiveTab('music')}
        >
          Music
        </button>
        <button 
          className={activeTab === 'soundeffects' ? 'active' : ''} 
          onClick={() => setActiveTab('soundeffects')}
        >
          Sound Effects
        </button>
        <button 
          className={activeTab === 'storage' ? 'active' : ''} 
          onClick={() => setActiveTab('storage')}
        >
          Storage
        </button>
      </nav>

      <main className="page-content">
        {activeTab === 'player' && (
          <div className="player-view">
            <NowPlaying status={playbackStatus} />
            <PlaybackControls status={playbackStatus} onUpdate={() => {}} />
          </div>
        )}
        
        {activeTab === 'tracks' && (
          <TrackTimesEditor />
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
        
        {activeTab === 'storage' && (
          <StorageManager />
        )}
      </main>
    </div>
  );
}

export default AudioPage;
