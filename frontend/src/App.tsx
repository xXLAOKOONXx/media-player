import { useState, useEffect } from 'react';
import './App.css';
import StorageManager from './components/StorageManager';
import LibraryManager from './components/LibraryManager';
import PlaybackControls from './components/PlaybackControls';
import NowPlaying from './components/NowPlaying';

// Use relative URL - works for both dev (proxied) and production (same origin)
const API_BASE_URL = '';

function App() {
  const [activeTab, setActiveTab] = useState<'storage' | 'library' | 'player'>('player');
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
    <div className="App">
      <header className="App-header">
        <h1>🎵 Media Player</h1>
        <nav className="tabs">
          <button 
            className={activeTab === 'player' ? 'active' : ''} 
            onClick={() => setActiveTab('player')}
          >
            Player
          </button>
          <button 
            className={activeTab === 'library' ? 'active' : ''} 
            onClick={() => setActiveTab('library')}
          >
            Library
          </button>
          <button 
            className={activeTab === 'storage' ? 'active' : ''} 
            onClick={() => setActiveTab('storage')}
          >
            Storage
          </button>
        </nav>
      </header>

      <main className="App-main">
        {activeTab === 'player' && (
          <div className="player-view">
            <NowPlaying status={playbackStatus} />
            <PlaybackControls status={playbackStatus} onUpdate={() => {}} />
          </div>
        )}
        
        {activeTab === 'library' && (
          <LibraryManager />
        )}
        
        {activeTab === 'storage' && (
          <StorageManager />
        )}
      </main>
    </div>
  );
}

export default App;
