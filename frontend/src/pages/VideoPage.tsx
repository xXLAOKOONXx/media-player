import { useState, useEffect, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import type { User } from '../types';
import './VideoPage.css';
import VideoLibrary from '../components/VideoLibrary';
import VideoPlaylistManager from '../components/VideoPlaylistManager';
import VideoPlayer from '../components/VideoPlayer';
import VideoPlaybackControls from '../components/VideoPlaybackControls';
import SettingsManager from '../components/SettingsManager';
import VideoExplorer from '../components/VideoExplorer';
import VideoSeries from '../components/VideoSeries';
import PageMenu from '../components/PageMenu';
import { useWebSocketStatus } from '../hooks/useWebSocketStatus';
import { useInterpolatedPosition } from '../hooks/useInterpolatedPosition';

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
    if (path.includes('/series')) return 'series';
    if (path.includes('/explorer')) return 'explorer';
    if (path.includes('/player')) return 'player';
    if (path.includes('/playlists')) return 'playlists';
    if (path.includes('/library')) return 'library';
    if (path.includes('/settings')) return 'settings';
    return 'player'; // default
  };

  const [activeTab, setActiveTab] = useState<'library' | 'playlists' | 'player' | 'settings' | 'explorer' | 'series'>(getActiveTabFromPath());
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

  // Use WebSocket for real-time status updates instead of polling
  const handleStatusUpdate = useCallback((status: any) => {
    setPlaybackStatus(status);
  }, []);

  useWebSocketStatus({
    eventName: 'video_status',
    onStatusUpdate: handleStatusUpdate,
    enabled: true,
  });

  // Interpolate position between WebSocket updates for smooth progress
  const interpolatedStatus = useInterpolatedPosition(playbackStatus);

  // Fallback: fetch initial status on mount
  useEffect(() => {
    fetch(`${API_BASE_URL}/api/video/playback/status`)
      .then(res => res.json())
      .then(data => setPlaybackStatus(data))
      .catch(err => console.error('Error fetching initial status:', err));
  }, []);

  return (
    <div className="video-page">
      <PageMenu
        items={[
          { key: 'player', label: 'Player' },
          { key: 'series', label: 'Series' },
          { key: 'explorer', label: 'Explorer' },
          { key: 'playlists', label: 'Playlists' },
          { key: 'library', label: 'Library' },
          { key: 'settings', label: 'Settings' },
        ]}
        activeKey={activeTab}
        onSelect={handleTabChange}
        storageKey="video.pageMenu"
        ariaLabel="Video menu"
      />

      <main className="video-main">
        {activeTab === 'player' && (
          <div className="player-view">
            <VideoPlayer status={interpolatedStatus} />
            <VideoPlaybackControls status={interpolatedStatus} onUpdate={() => {}} />
          </div>
        )}

        {activeTab === 'explorer' && (
          <VideoExplorer />
        )}

        {activeTab === 'series' && (
          <VideoSeries />
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
