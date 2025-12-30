import { useState, useEffect } from 'react';
import type { User } from '../types';
import UserManagement from './UserManagement';
import './SettingsManager.css';

const API_BASE_URL = '';

const PREFERRED_LANGUAGE_OPTIONS = ['deu', 'eng'] as const;
type PreferredLanguage = typeof PREFERRED_LANGUAGE_OPTIONS[number];

interface Settings {
  crossfade: {
    enabled: boolean;
    duration_ms: number;
    fade_out_start_before_end_ms: number;
  };
  video: {
    fullscreen: boolean;
    preferred_screen: number | string | null;
  };
  stats_folder: string;
}

interface SettingsManagerProps {
  currentUser?: User | null;
}

const SettingsManager = ({ currentUser }: SettingsManagerProps) => {
  const [settings, setSettings] = useState<Settings>({
    crossfade: {
      enabled: true,
      duration_ms: 3000,
      fade_out_start_before_end_ms: 5000
    },
    video: {
      fullscreen: true,
      preferred_screen: null
    },
    stats_folder: ''
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [preferredLanguage, setPreferredLanguage] = useState<PreferredLanguage>('eng');
  const [savingPreferredLanguage, setSavingPreferredLanguage] = useState(false);

  useEffect(() => {
    loadSettings();
    loadUserPreferences();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/settings`, { credentials: 'include' });
      if (response.ok) {
        const data = await response.json();
        setSettings(data);
      } else {
        console.error('Failed to load settings');
      }
    } catch (error) {
      console.error('Error loading settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadUserPreferences = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/user/preferences`, { credentials: 'include' });
      if (response.ok) {
        const data = await response.json();
        const value = data?.preferred_language;
        if (PREFERRED_LANGUAGE_OPTIONS.includes(value)) {
          setPreferredLanguage(value);
        }
      }
    } catch (error) {
      console.error('Error loading user preferences:', error);
    }
  };

  const saveUserPreferences = async (value: PreferredLanguage) => {
    try {
      setSavingPreferredLanguage(true);
      const response = await fetch(`${API_BASE_URL}/api/user/preferences`, {
        method: 'PUT',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ preferred_language: value }),
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        alert(`Failed to save preferred language: ${error.error || 'Unknown error'}`);
        return false;
      }
      return true;
    } catch (error) {
      console.error('Error saving user preferences:', error);
      alert('Failed to save preferred language. Please try again.');
      return false;
    } finally {
      setSavingPreferredLanguage(false);
    }
  };

  const saveSettings = async () => {
    try {
      setSaving(true);
      const response = await fetch(`${API_BASE_URL}/api/settings`, {
        method: 'PUT',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(settings),
      });

      if (response.ok) {
        alert('Settings saved successfully!');
      } else {
        const error = await response.json();
        alert(`Failed to save settings: ${error.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error saving settings:', error);
      alert('Failed to save settings. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const handleCrossfadeEnabledChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSettings({
      ...settings,
      crossfade: {
        ...settings.crossfade,
        enabled: e.target.checked
      }
    });
  };

  const handleCrossfadeDurationChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value) || 0;
    setSettings({
      ...settings,
      crossfade: {
        ...settings.crossfade,
        duration_ms: value
      }
    });
  };

  const handleCrossfadeFadeOutChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value) || 0;
    setSettings({
      ...settings,
      crossfade: {
        ...settings.crossfade,
        fade_out_start_before_end_ms: value
      }
    });
  };

  const handleVideoFullscreenChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSettings({
      ...settings,
      video: {
        ...settings.video,
        fullscreen: e.target.checked
      }
    });
  };

  const handleVideoPreferredScreenChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    setSettings({
      ...settings,
      video: {
        ...settings.video,
        preferred_screen: value === 'none' ? null : parseInt(value)
      }
    });
  };

  const handleStatsFolderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSettings({
      ...settings,
      stats_folder: e.target.value
    });
  };

  const browseStatsFolder = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/browse`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ path: settings.stats_folder || '' }),
      });

      if (response.ok) {
        const data = await response.json();
        const selectedPath = prompt('Enter folder path:', data.current_path);
        if (selectedPath) {
          setSettings({
            ...settings,
            stats_folder: selectedPath
          });
        }
      }
    } catch (error) {
      console.error('Error browsing folder:', error);
    }
  };

  if (loading) {
    return (
      <div className="settings-manager">
        <div className="loading">Loading settings...</div>
      </div>
    );
  }

  return (
    <div className="settings-manager">
      <h2>Settings</h2>

      {/* User Preferences Section */}
      <section className="settings-section">
        <h3>User Preferences</h3>
        <div className="settings-group">
          <div className="setting-item">
            <label>
              <span className="setting-label">Preferred language:</span>
              <select
                value={preferredLanguage}
                onChange={async (e) => {
                  const next = e.target.value as PreferredLanguage;
                  const prev = preferredLanguage;
                  setPreferredLanguage(next);
                  const ok = await saveUserPreferences(next);
                  if (!ok) setPreferredLanguage(prev);
                }}
                disabled={savingPreferredLanguage}
              >
                {PREFERRED_LANGUAGE_OPTIONS.map((lang) => (
                  <option key={lang} value={lang}>
                    {lang}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </div>
      </section>

      {/* Audio Settings Section */}
      <section className="settings-section">
        <h3>Audio Settings</h3>
        
        <div className="settings-group">
          <h4>Crossfade</h4>
          
          <div className="setting-item">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={settings.crossfade.enabled}
                onChange={handleCrossfadeEnabledChange}
              />
              <span>Enable crossfade between tracks</span>
            </label>
          </div>

          <div className="setting-item">
            <label>
              <span className="setting-label">Crossfade duration (ms):</span>
              <input
                type="number"
                min="0"
                step="100"
                value={settings.crossfade.duration_ms}
                onChange={handleCrossfadeDurationChange}
                disabled={!settings.crossfade.enabled}
              />
            </label>
            <p className="setting-description">
              How long the fade effect between tracks should last
            </p>
          </div>

          <div className="setting-item">
            <label>
              <span className="setting-label">Start fade before track end (ms):</span>
              <input
                type="number"
                min="0"
                step="100"
                value={settings.crossfade.fade_out_start_before_end_ms}
                onChange={handleCrossfadeFadeOutChange}
                disabled={!settings.crossfade.enabled}
              />
            </label>
            <p className="setting-description">
              When to start fading out the current track before it ends
            </p>
          </div>
        </div>
      </section>

      {/* Video Settings Section */}
      <section className="settings-section">
        <h3>Video Settings</h3>
        
        <div className="settings-group">
          <h4>Playback</h4>
          
          <div className="setting-item">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={settings.video.fullscreen}
                onChange={handleVideoFullscreenChange}
              />
              <span>Open videos in fullscreen mode</span>
            </label>
            <p className="setting-description">
              When enabled, videos will automatically play in fullscreen
            </p>
          </div>

          <div className="setting-item">
            <label>
              <span className="setting-label">Preferred screen:</span>
              <select
                value={settings.video.preferred_screen === null ? 'none' : settings.video.preferred_screen}
                onChange={handleVideoPreferredScreenChange}
              >
                <option value="none">None (use default)</option>
                <option value="0">Screen 0 (Primary)</option>
                <option value="1">Screen 1</option>
                <option value="2">Screen 2</option>
                <option value="3">Screen 3</option>
              </select>
            </label>
            <p className="setting-description">
              Which screen to display videos on (if multiple displays are available)
            </p>
          </div>
        </div>
      </section>

      {/* Stats Settings Section - Admin Only */}
      {currentUser?.role === 'admin' && (
        <section className="settings-section">
          <h3>Statistics Settings</h3>
          
          <div className="settings-group">
            <h4>Playback Statistics</h4>
            
            <div className="setting-item">
              <label>
                <span className="setting-label">Stats database folder:</span>
                <div className="path-input-group">
                  <input
                    type="text"
                    value={settings.stats_folder}
                    onChange={handleStatsFolderChange}
                    placeholder="/path/to/stats/folder"
                  />
                  <button
                    type="button"
                    className="btn-secondary"
                    onClick={browseStatsFolder}
                  >
                    Browse
                  </button>
                </div>
              </label>
              <p className="setting-description">
                Folder where the media-player-stats.db file will be stored. 
                Leave empty to use the default location (backend directory).
              </p>
            </div>
          </div>
        </section>
      )}

      {/* Save Button - Admin Only */}
      {currentUser?.role === 'admin' && (
        <div className="settings-actions">
          <button
            className="btn-primary"
            onClick={saveSettings}
            disabled={saving}
          >
            {saving ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      )}

      {/* User Management Section - Admin Only */}
      {currentUser?.role === 'admin' && (
        <section className="settings-section">
          <UserManagement currentUser={currentUser} />
        </section>
      )}
    </div>
  );
};

export default SettingsManager;
