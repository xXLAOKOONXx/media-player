import { useState, useEffect, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import type { User } from '../types';
import PlaylistManager from '../components/PlaylistManager';
import PlaybackControls from '../components/PlaybackControls';
import NowPlaying from '../components/NowPlaying';
import SoundEffectsManager from '../components/SoundEffectsManager';
import MusicManager from '../components/MusicManager';
import SettingsManager from '../components/SettingsManager';
import PageMenu from '../components/PageMenu';
import { useSSEStatus } from '../hooks/useSSEStatus';
import { useInterpolatedPosition } from '../hooks/useInterpolatedPosition';

// Use relative URL - works for both dev (proxied) and production (same origin)
const API_BASE_URL = '';

interface AudioPageProps {
  currentUser: User;
}

function AudioPage({ currentUser }: AudioPageProps) {
  const navigate = useNavigate();
  const location = useLocation();
  
  // Derive active tab from URL path
  const getActiveTabFromPath = () => {
    const path = location.pathname;
    if (path.includes('/player')) return 'player';
    if (path.includes('/playlists')) return 'playlists';
    if (path.includes('/music')) return 'music';
    if (path.includes('/soundeffects')) return 'soundeffects';
    if (path.includes('/settings')) return 'settings';
    return 'player'; // default
  };

  const [activeTab, setActiveTab] = useState<'playlists' | 'player' | 'soundeffects' | 'music' | 'settings'>(getActiveTabFromPath());
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

  // Use SSE for real-time status updates
  const handleStatusUpdate = useCallback((status: any) => {
    setPlaybackStatus(status);
  }, []);

  useSSEStatus({
    endpoint: '/api/audio/playback/events',
    onStatusUpdate: handleStatusUpdate,
    enabled: true,
  });

  // Interpolate position between SSE updates for smooth progress
  const interpolatedStatus = useInterpolatedPosition(playbackStatus);

  // Fallback: fetch initial status on mount
  useEffect(() => {
    fetch(`${API_BASE_URL}/api/audio/playback/status`)
      .then(res => res.json())
      .then(data => setPlaybackStatus(data))
      .catch(err => console.error('Error fetching initial status:', err));
  }, []);

  return (
    <div className="audio-page">
      <PageMenu
        items={[
          { key: 'player', label: 'Player' },
          { key: 'playlists', label: 'Playlists' },
          { key: 'music', label: 'Music' },
          { key: 'soundeffects', label: 'Sound Effects' },
          { key: 'settings', label: 'Settings' },
        ]}
        activeKey={activeTab}
        onSelect={handleTabChange}
        storageKey="audio.pageMenu"
        ariaLabel="Audio menu"
      />

      <main className="App-main">
        {activeTab === 'player' && (
          <div className="player-view">
            <NowPlaying status={interpolatedStatus} />
            <PlaybackControls status={interpolatedStatus} onUpdate={() => {}} />
          </div>
        )}
        
        {activeTab === 'playlists' && (
          <PlaylistManager currentUser={currentUser} />
        )}
        
        {activeTab === 'music' && (
          <MusicManager currentUser={currentUser} />
        )}
        
        {activeTab === 'soundeffects' && (
          <SoundEffectsManager currentUser={currentUser} />
        )}
        
        {activeTab === 'settings' && (
          <SettingsManager currentUser={currentUser} />
        )}
      </main>
    </div>
  );
}

export default AudioPage;
