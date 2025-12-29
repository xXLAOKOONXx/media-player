import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import './VideoExplorer.css';
import './VideoSeries.css';

const API_BASE_URL = '';

interface VideoLibrary {
  id: number;
  name: string;
  path: string;
  recursive: boolean;
  storage_id?: number;
}

interface Video {
  name?: string;
  path?: string;
  title?: string;
  duration?: number;
  media_id?: string;
  has_thumbnail?: boolean;
  thumbnail_url?: string;
  artist?: string;
  tags?: string[];
  user_rating?: number;
  index_number?: number;
}

interface Season {
  full_path: string;
  title: string;
  user_rating?: number | null;
  tags?: string[];
  artists?: string[];
  cover?: string | null;
  index_number?: number | null;
  videos: Video[];
}

interface Series {
  full_path: string;
  title: string;
  user_rating?: number | null;
  tags?: string[];
  artists?: string[];
  cover?: string | null;
  seasons: Season[];
  videos: Video[];
}

const DEFAULT_LIBRARY_STORAGE_KEY = 'videoSeries.defaultLibraryId';

const getVideoTitle = (video: Video) => (video.title || video.name || 'Untitled').trim();

const formatDuration = (seconds?: number) => {
  if (seconds == null || Number.isNaN(seconds)) return '—';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
};

const normalizeCoverSrc = (cover?: string | null) => {
  if (!cover) return null;
  // API-relative covers (e.g. /api/video/thumbnail/by-id/...) should stay relative to API_BASE_URL
  if (cover.startsWith('/')) return `${API_BASE_URL}${cover}`;
  return cover;
};

function VideoSeries() {
  const [libraries, setLibraries] = useState<VideoLibrary[]>([]);
  const [selectedLibraryId, setSelectedLibraryId] = useState<number | null>(null);
  const [defaultLibraryId, setDefaultLibraryId] = useState<number | null>(null);

  const [seriesList, setSeriesList] = useState<Series[]>([]);
  const [isLoadingLibraries, setIsLoadingLibraries] = useState(false);
  const [isLoadingSeries, setIsLoadingSeries] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [searchParams, setSearchParams] = useSearchParams();

  const selectedSeriesPath = searchParams.get('series') || '';
  const selectedSeasonPath = searchParams.get('season') || '';

  useEffect(() => {
    const stored = window.localStorage.getItem(DEFAULT_LIBRARY_STORAGE_KEY);
    if (stored && stored.trim()) {
      const parsed = Number(stored);
      if (!Number.isNaN(parsed)) setDefaultLibraryId(parsed);
    }
  }, []);

  useEffect(() => {
    const loadLibraries = async () => {
      setIsLoadingLibraries(true);
      setError(null);
      try {
        const response = await fetch(`${API_BASE_URL}/api/video/libraries`);
        const data = await response.json();
        setLibraries(Array.isArray(data) ? data : []);
      } catch (e) {
        setError('Failed to load video libraries');
      } finally {
        setIsLoadingLibraries(false);
      }
    };

    loadLibraries();
  }, []);

  useEffect(() => {
    if (libraries.length === 0) {
      setSelectedLibraryId(null);
      return;
    }

    if (selectedLibraryId && libraries.some(l => l.id === selectedLibraryId)) {
      return;
    }

    if (defaultLibraryId && libraries.some(l => l.id === defaultLibraryId)) {
      setSelectedLibraryId(defaultLibraryId);
      return;
    }

    setSelectedLibraryId(libraries[0].id);
  }, [libraries, defaultLibraryId, selectedLibraryId]);

  const setAsDefaultLibrary = (libraryId: number) => {
    setDefaultLibraryId(libraryId);
    window.localStorage.setItem(DEFAULT_LIBRARY_STORAGE_KEY, String(libraryId));
  };

  useEffect(() => {
    const loadSeries = async (libraryId: number) => {
      setIsLoadingSeries(true);
      setError(null);
      try {
        const response = await fetch(`${API_BASE_URL}/api/video/libraries/${libraryId}/series`);
        const data = await response.json();
        setSeriesList(Array.isArray(data) ? data : []);
      } catch (e) {
        setError('Failed to load series for the selected library');
        setSeriesList([]);
      } finally {
        setIsLoadingSeries(false);
      }
    };

    if (selectedLibraryId != null) {
      loadSeries(selectedLibraryId);
    } else {
      setSeriesList([]);
    }
  }, [selectedLibraryId]);

  const selectedSeries = useMemo(() => {
    if (!selectedSeriesPath) return null;
    return seriesList.find(s => s.full_path === selectedSeriesPath) || null;
  }, [seriesList, selectedSeriesPath]);

  const selectedSeason = useMemo(() => {
    if (!selectedSeries) return null;
    if (!selectedSeasonPath) return null;
    return selectedSeries.seasons?.find(se => se.full_path === selectedSeasonPath) || null;
  }, [selectedSeasonPath, selectedSeries]);

  const closeModal = () => {
    const next = new URLSearchParams(searchParams);
    next.delete('series');
    next.delete('season');
    setSearchParams(next);
  };

  const openSeries = (s: Series) => {
    const next = new URLSearchParams(searchParams);
    next.set('series', s.full_path);
    next.delete('season');
    setSearchParams(next);
  };

  const selectSeason = (season: Season) => {
    const next = new URLSearchParams(searchParams);
    if (selectedSeries) next.set('series', selectedSeries.full_path);
    next.set('season', season.full_path);
    setSearchParams(next);
  };

  const startPlayback = async (video: Video) => {
    try {
      if (!video.media_id) {
        setError('Missing media_id for selected video');
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
        setError(msg);
        return;
      }
    } catch (e) {
      setError('Failed to start playback');
    }
  };

  const renderVideoList = (videos: Video[]) => {
    const items = Array.isArray(videos) ? videos : [];
    if (items.length === 0) return <div className="video-explorer-empty">No videos found.</div>;

    return (
      <div className="video-series-episode-list">
        {items.map((v) => {
          const title = getVideoTitle(v);
          const idx = typeof v.index_number === 'number' ? v.index_number : null;
          return (
            <div key={v.media_id || v.path || title} className="video-series-episode-row">
              <div className="video-series-episode-main">
                <div className="video-series-episode-title">
                  {idx != null ? <span className="video-series-episode-index">{idx}.</span> : null}
                  <span>{title}</span>
                </div>
                <div className="video-series-episode-meta">{formatDuration(v.duration)}</div>
              </div>
              <div className="video-series-episode-actions">
                <button type="button" className="btn" onClick={() => startPlayback(v)}>
                  <span className="material-icons">play_arrow</span>
                  Play
                </button>
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="video-explorer">
      <div className="card video-explorer-card">
        <h2>Video Series</h2>

        {error && (
          <div className="video-explorer-error">
            <span className="material-icons">error_outline</span>
            <span>{error}</span>
          </div>
        )}

        <div className="video-explorer-libraries">
          <h3>Video Libraries</h3>

          {isLoadingLibraries ? (
            <div className="video-explorer-loading">Loading libraries…</div>
          ) : libraries.length === 0 ? (
            <div className="video-explorer-empty">No video libraries configured.</div>
          ) : (
            <div className="video-explorer-library-grid">
              {libraries.map((lib) => {
                const isSelected = selectedLibraryId === lib.id;
                const isDefault = defaultLibraryId === lib.id;

                return (
                  <button
                    key={lib.id}
                    type="button"
                    className={`video-explorer-library-btn ${isSelected ? 'selected' : ''}`}
                    onClick={() => setSelectedLibraryId(lib.id)}
                    title={lib.path}
                  >
                    <span className="video-explorer-library-name">{lib.name}</span>
                    <span className="video-explorer-library-spacer" />
                    <button
                      type="button"
                      className={`video-explorer-star-btn ${isDefault ? 'active' : ''}`}
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        setAsDefaultLibrary(lib.id);
                      }}
                      aria-label={isDefault ? 'Default folder' : 'Set as default folder'}
                      title={isDefault ? 'Default folder' : 'Set as default'}
                    >
                      <span className="material-icons">{isDefault ? 'star' : 'star_border'}</span>
                    </button>
                  </button>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {selectedLibraryId != null && (
        <div className="video-explorer-browse">
          <div className="video-explorer-browse-header">
            {isLoadingSeries && <div className="video-explorer-loading">Loading series…</div>}
          </div>

          {!isLoadingSeries && seriesList.length === 0 ? (
            <div className="card">
              <div className="video-explorer-empty">No series found in this library.</div>
              <div className="video-series-hint">
                Series are inferred from folder structure when the library is configured as recursive.
              </div>
            </div>
          ) : (
            <div className="card">
              <div className="video-series-grid">
                {seriesList.map((s) => {
                  const cover = normalizeCoverSrc(s.cover);
                  const showCover = !!cover;
                  const title = (s.title || 'Untitled').trim();
                  return (
                    <button
                      key={s.full_path}
                      type="button"
                      className="video-series-tile video-explorer-thumb"
                      onClick={() => openSeries(s)}
                      title={title}
                    >
                      <div className="video-explorer-thumb-image video-series-tile-image">
                        {showCover ? (
                          <img src={cover} alt={title} loading="lazy" />
                        ) : (
                          <div className="video-explorer-thumb-placeholder">
                            <span className="material-icons">collections</span>
                          </div>
                        )}
                        <div className="video-explorer-thumb-title" aria-hidden>
                          {title}
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}

      {selectedSeries && (
        <div
          className="video-explorer-modal-overlay"
          role="dialog"
          aria-modal="true"
          onMouseDown={(e) => {
            if (e.target === e.currentTarget) closeModal();
          }}
        >
          <div className="card video-explorer-modal">
            <div className="video-explorer-modal-header">
              <h3>{selectedSeries.title}</h3>
              <button type="button" className="video-explorer-modal-close" onClick={closeModal} aria-label="Close">
                <span className="material-icons">close</span>
              </button>
            </div>

            <div className="video-explorer-modal-body">
              {(() => {
                const cover = normalizeCoverSrc(selectedSeries.cover);
                if (cover) {
                  return (
                    <div className="video-explorer-modal-cover">
                      <img src={cover} alt={selectedSeries.title} />
                    </div>
                  );
                }
                return (
                  <div className="video-explorer-modal-cover">
                    <div className="video-explorer-modal-cover-placeholder" aria-hidden>
                      <span className="material-icons">collections</span>
                    </div>
                  </div>
                );
              })()}

              {Array.isArray(selectedSeries.seasons) && selectedSeries.seasons.length > 0 && (
                <div className="video-series-seasons">
                  <h4>Seasons</h4>
                  <div className="video-series-season-buttons">
                    {selectedSeries.seasons.map((se) => (
                      <button
                        key={se.full_path}
                        type="button"
                        className={`btn ${selectedSeason?.full_path === se.full_path ? 'active' : ''}`}
                        onClick={() => selectSeason(se)}
                      >
                        {se.title}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {selectedSeason ? (
                <div className="video-series-episodes">
                  <h4>{selectedSeason.title}</h4>
                  {renderVideoList(selectedSeason.videos)}
                </div>
              ) : (
                <div className="video-series-episodes">
                  <h4>Videos</h4>
                  {renderVideoList(selectedSeries.videos)}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default VideoSeries;
