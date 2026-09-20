import { useEffect, useMemo, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import './VideoExplorer.css';
import './VideoSeries.css';
import VideoSeriesModal from './VideoSeriesModal';
import {
  getSeriesWatchedState,
  normalizeCoverSrc,
} from './videoSeriesShared';
import type { Series, Season, Video } from './videoSeriesShared';

const API_BASE_URL = '';

interface VideoLibrary {
  id: number;
  name: string;
  path: string;
  recursive: boolean;
  storage_id?: number;
}

const DEFAULT_LIBRARY_STORAGE_KEY = 'videoSeries.defaultLibraryId';

const RECENT_SERIES_ROW_KEY = '__recent_series__';

const SERIES_ID_QUERY_KEY = 'seriesId';
const SEASON_ID_QUERY_KEY = 'seasonId';
const LIBRARY_ID_QUERY_KEY = 'libraryId';
// Backward-compatibility for old deep-links.
const SERIES_PATH_QUERY_KEY = 'series';
const SEASON_PATH_QUERY_KEY = 'season';

const getSeriesPromotionScore = (series: Series) => {
  let maxScore = 0;
  let hasAnyScore = false;

  const consider = (video: Video) => {
    const score = video.promotion_score;
    if (score == null || !Number.isFinite(score)) return;
    if (!hasAnyScore) {
      maxScore = score;
      hasAnyScore = true;
      return;
    }
    if (score > maxScore) maxScore = score;
  };

  for (const v of series.videos || []) consider(v);
  for (const season of series.seasons || []) {
    for (const v of season.videos || []) consider(v);
  }

  return hasAnyScore ? maxScore : 0;
};

function VideoSeries() {
  const [libraries, setLibraries] = useState<VideoLibrary[]>([]);
  const [selectedLibraryId, setSelectedLibraryId] = useState<number | null>(null);
  const [defaultLibraryId, setDefaultLibraryId] = useState<number | null>(null);

  const [isLibraryPickerOpen, setIsLibraryPickerOpen] = useState(false);

  const [seriesList, setSeriesList] = useState<Series[]>([]);
  const [isLoadingLibraries, setIsLoadingLibraries] = useState(false);
  const [isLoadingSeries, setIsLoadingSeries] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [, setBrokenThumbnails] = useState<Set<string>>(new Set());
  const [thumbnailAspectRatios, setThumbnailAspectRatios] = useState<Map<string, number>>(new Map());

  const [seriesCarouselScrollState, setSeriesCarouselScrollState] = useState<
    Record<string, { canScrollLeft: boolean; canScrollRight: boolean }>
  >({});

  const seriesCarouselRefs = useRef<Record<string, HTMLDivElement | null>>({});

  const CAROUSEL_TILE_HEIGHT_PX = 210;

  const [searchParams, setSearchParams] = useSearchParams();

  const selectedLibraryIdFromUrlRaw = searchParams.get(LIBRARY_ID_QUERY_KEY) || '';
  const selectedLibraryIdFromUrl = (() => {
    if (!selectedLibraryIdFromUrlRaw) return null;
    const parsed = Number(selectedLibraryIdFromUrlRaw);
    return Number.isFinite(parsed) ? parsed : null;
  })();

  const selectedSeriesId = searchParams.get(SERIES_ID_QUERY_KEY) || '';
  const selectedSeasonId = searchParams.get(SEASON_ID_QUERY_KEY) || '';
  const selectedSeriesPath = searchParams.get(SERIES_PATH_QUERY_KEY) || '';
  const selectedSeasonPath = searchParams.get(SEASON_PATH_QUERY_KEY) || '';

  const updateSeriesCarouselScrollState = (rowKey: string) => {
    const el = seriesCarouselRefs.current[rowKey];
    if (!el) return;
    const canScrollLeft = el.scrollLeft > 1;
    const canScrollRight = el.scrollLeft + el.clientWidth < el.scrollWidth - 1;
    setSeriesCarouselScrollState(prev => {
      const existing = prev[rowKey];
      if (existing && existing.canScrollLeft === canScrollLeft && existing.canScrollRight === canScrollRight) {
        return prev;
      }
      return { ...prev, [rowKey]: { canScrollLeft, canScrollRight } };
    });
  };

  const scrollSeriesCarousel = (rowKey: string, direction: -1 | 1) => {
    const el = seriesCarouselRefs.current[rowKey];
    if (!el) return;
    el.scrollBy({ left: direction * 420, behavior: 'smooth' });
    window.setTimeout(() => updateSeriesCarouselScrollState(rowKey), 350);
  };

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
      } catch {
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

    // URL takes priority (shareable links).
    if (selectedLibraryIdFromUrl != null && libraries.some(l => l.id === selectedLibraryIdFromUrl)) {
      if (selectedLibraryId === null) {
        setSelectedLibraryId(selectedLibraryIdFromUrl);
      }
      return;
    }

    if (selectedLibraryId && libraries.some(l => l.id === selectedLibraryId)) return;

    if (defaultLibraryId && libraries.some(l => l.id === defaultLibraryId)) {
      setSelectedLibraryId(defaultLibraryId);
      return;
    }

    setSelectedLibraryId(libraries[0].id);
  }, [libraries, defaultLibraryId, selectedLibraryId, selectedLibraryIdFromUrl]);

  // Keep library selection in the URL.
  // Important: this must use the latest `searchParams` to avoid re-introducing stale series/season params,
  // which can otherwise cause the URL + selection to "fight" and appear to jump back and forth.
  useEffect(() => {
    if (selectedLibraryId == null) return;
    if (selectedLibraryIdFromUrl === selectedLibraryId) return;

    const next = new URLSearchParams(searchParams);
    next.set(LIBRARY_ID_QUERY_KEY, String(selectedLibraryId));

    // Changing libraries invalidates any selected series/season.
    next.delete(SERIES_ID_QUERY_KEY);
    next.delete(SEASON_ID_QUERY_KEY);
    next.delete(SERIES_PATH_QUERY_KEY);
    next.delete(SEASON_PATH_QUERY_KEY);

    setSearchParams(next, { replace: true });
  }, [searchParams, selectedLibraryId, selectedLibraryIdFromUrl, setSearchParams]);

  const setAsDefaultLibrary = (libraryId: number) => {
    setDefaultLibraryId(libraryId);
    window.localStorage.setItem(DEFAULT_LIBRARY_STORAGE_KEY, String(libraryId));
  };

  const selectedLibraryName = useMemo(() => {
    const lib = libraries.find(l => l.id === selectedLibraryId);
    return (lib?.name || '').trim() || 'Select library';
  }, [libraries, selectedLibraryId]);

  useEffect(() => {
    const loadSeries = async (libraryId: number) => {
      setIsLoadingSeries(true);
      setError(null);
      try {
        const response = await fetch(`${API_BASE_URL}/api/video/libraries/${libraryId}/series`);
        const data = await response.json();
        setSeriesList(Array.isArray(data) ? data : []);
      } catch {
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

  const seriesTags = useMemo(() => {
    const set = new Set<string>();
    for (const s of seriesList) {
      for (const t of s.tags || []) {
        const trimmed = (t || '').trim();
        if (trimmed) set.add(trimmed);
      }
    }

    // Randomize tag row order (stable until `seriesList` changes), matching Video Explorer behavior.
    const arr = Array.from(set);
    for (let i = arr.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [arr[i], arr[j]] = [arr[j], arr[i]];
    }
    return arr;
  }, [seriesList]);

  const seriesByTag = useMemo(() => {
    const map = new Map<string, Series[]>();
    for (const tag of seriesTags) map.set(tag, []);
    for (const s of seriesList) {
      for (const t of s.tags || []) {
        const trimmed = (t || '').trim();
        if (!trimmed) continue;
        if (!map.has(trimmed)) map.set(trimmed, []);
        map.get(trimmed)?.push(s);
      }
    }

    for (const bucket of map.values()) {
      bucket.sort((a, b) => {
        const aScore = getSeriesPromotionScore(a);
        const bScore = getSeriesPromotionScore(b);
        if (bScore !== aScore) return bScore - aScore;

        const byTitle = (a.title || '').localeCompare(b.title || '');
        if (byTitle) return byTitle;
        return (a.full_path || '').localeCompare(b.full_path || '');
      });
    }

    return map;
  }, [seriesList, seriesTags]);

  const recentSeries = useMemo(() => {
    const items = seriesList
      .map((s) => {
        const all: Video[] = [];
        if (Array.isArray(s.videos)) all.push(...s.videos);
        if (Array.isArray(s.seasons)) {
          for (const season of s.seasons) {
            if (Array.isArray(season.videos)) all.push(...season.videos);
          }
        }
        let maxLastPlayed: number | null = null;
        for (const v of all) {
          const lp = v.last_played;
          if (lp == null || !Number.isFinite(lp)) continue;
          if (maxLastPlayed == null || lp > maxLastPlayed) maxLastPlayed = lp;
        }
        return { series: s, maxLastPlayed };
      })
      .filter(x => x.maxLastPlayed != null)
      .sort((a, b) => (b.maxLastPlayed as number) - (a.maxLastPlayed as number))
      .slice(0, 10)
      .map(x => x.series);

    return items;
  }, [seriesList]);

  const selectedSeries = useMemo(() => {
    if (selectedSeriesId) {
      const byId = seriesList.find(s => s.id === selectedSeriesId);
      if (byId) return byId;
    }
    if (selectedSeriesPath) {
      return seriesList.find(s => s.full_path === selectedSeriesPath) || null;
    }
    return null;
  }, [seriesList, selectedSeriesId, selectedSeriesPath]);

  const selectedSeason = useMemo(() => {
    if (!selectedSeries) return null;
    if (selectedSeasonId) {
      const byId = selectedSeries.seasons?.find(se => se.id === selectedSeasonId) || null;
      if (byId) return byId;
    }
    if (selectedSeasonPath) {
      return selectedSeries.seasons?.find(se => se.full_path === selectedSeasonPath) || null;
    }
    return null;
  }, [selectedSeasonId, selectedSeasonPath, selectedSeries]);

  const closeModal = () => {
    const next = new URLSearchParams(searchParams);
    next.delete(SERIES_ID_QUERY_KEY);
    next.delete(SEASON_ID_QUERY_KEY);
    next.delete(SERIES_PATH_QUERY_KEY);
    next.delete(SEASON_PATH_QUERY_KEY);
    setSearchParams(next);
  };

  const openSeries = (s: Series) => {
    const next = new URLSearchParams(searchParams);
    if (s.id) next.set(SERIES_ID_QUERY_KEY, s.id);
    next.delete(SEASON_ID_QUERY_KEY);
    next.delete(SERIES_PATH_QUERY_KEY);
    next.delete(SEASON_PATH_QUERY_KEY);
    setSearchParams(next);
  };

  const selectSeason = (season: Season) => {
    const next = new URLSearchParams(searchParams);
    if (selectedSeries?.id) next.set(SERIES_ID_QUERY_KEY, selectedSeries.id);
    if (season.id) next.set(SEASON_ID_QUERY_KEY, season.id);
    next.delete(SERIES_PATH_QUERY_KEY);
    next.delete(SEASON_PATH_QUERY_KEY);
    setSearchParams(next);
  };

  const handleCarouselWheel = (e: React.WheelEvent<HTMLDivElement>) => {
    if (e.shiftKey || Math.abs(e.deltaX) > 0) {
      e.preventDefault();
      e.stopPropagation();
    }
  };

  const getCardWidthPx = (key: string) => {
    const ratio = thumbnailAspectRatios.get(key) || (16 / 9);
    const safeRatio = Number.isFinite(ratio) && ratio > 0 ? ratio : (16 / 9);
    return Math.max(1, Math.round(CAROUSEL_TILE_HEIGHT_PX * safeRatio));
  };

  useEffect(() => {
    // Cover image loads can change widths; recompute arrow visibility on the next frame.
    const raf = window.requestAnimationFrame(() => {
      if (recentSeries.length > 0) updateSeriesCarouselScrollState(RECENT_SERIES_ROW_KEY);
      for (const tag of seriesTags) updateSeriesCarouselScrollState(tag);
    });
    return () => window.cancelAnimationFrame(raf);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [seriesTags, recentSeries.length, thumbnailAspectRatios]);

  const renderSeriesCarouselRow = (rowKey: string, title: string, items: Series[]) => {
    if (items.length === 0) return null;
    const canScrollLeft = seriesCarouselScrollState[rowKey]?.canScrollLeft ?? false;
    const canScrollRight = seriesCarouselScrollState[rowKey]?.canScrollRight ?? true;

    return (
      <div key={rowKey} className="video-explorer-carousel-section">
        <div className="video-explorer-carousel-title">
          <h4>{title}</h4>
        </div>

        <div className="video-explorer-carousel-container">
          {canScrollLeft && (
            <button
              type="button"
              className="video-explorer-carousel-arrow video-explorer-carousel-arrow-left"
              onClick={() => scrollSeriesCarousel(rowKey, -1)}
              aria-label={`Scroll ${title} left`}
            >
              <span className="material-icons">chevron_left</span>
            </button>
          )}

          <div
            className="video-explorer-carousel"
            onWheel={handleCarouselWheel}
            onScroll={() => updateSeriesCarouselScrollState(rowKey)}
            ref={(el) => {
              seriesCarouselRefs.current[rowKey] = el;
              if (el) window.requestAnimationFrame(() => updateSeriesCarouselScrollState(rowKey));
            }}
          >
            {items.map((s) => {
              const cover = normalizeCoverSrc(s.cover);
              const showCover = !!cover;
              const seriesTitle = (s.title || 'Untitled').trim();
              const watchedState = getSeriesWatchedState(s);
              const key = s.id || s.full_path;
              const brokenKey = key || seriesTitle;
              const cardWidth = getCardWidthPx(brokenKey);

              return (
                <button
                  key={`${brokenKey}-${rowKey}`}
                  type="button"
                  className="video-series-tile video-explorer-thumb"
                  onClick={() => openSeries(s)}
                  title={seriesTitle}
                  style={{ width: `${cardWidth}px` }}
                >
                  <div className="video-explorer-thumb-image video-series-tile-image">
                    {showCover ? (
                      <img
                        src={cover as string}
                        alt={seriesTitle}
                        loading="lazy"
                        onLoad={(e) => {
                          const img = e.currentTarget as HTMLImageElement;
                          const w = img.naturalWidth;
                          const h = img.naturalHeight;
                          if (!w || !h) return;
                          const ratio = w / h;
                          if (!Number.isFinite(ratio) || ratio <= 0) return;
                          setThumbnailAspectRatios(prev => {
                            if (prev.get(brokenKey) === ratio) return prev;
                            const next = new Map(prev);
                            next.set(brokenKey, ratio);
                            return next;
                          });
                        }}
                        onError={() => {
                          setBrokenThumbnails(prev => {
                            const next = new Set(prev);
                            next.add(brokenKey);
                            return next;
                          });
                        }}
                      />
                    ) : (
                      <div className="video-explorer-thumb-placeholder">
                        <span className="material-icons">collections</span>
                      </div>
                    )}

                    {watchedState.isStarted && (
                      <div className="video-series-thumb-status" aria-hidden title="Started watching">
                        <span className="material-icons">play_arrow</span>
                      </div>
                    )}
                    {watchedState.isFullyWatched && (
                      <div className="video-series-thumb-status" aria-hidden title="Fully watched">
                        <span className="material-icons">visibility</span>
                      </div>
                    )}

                    <div className="video-explorer-thumb-title" aria-hidden>
                      {seriesTitle}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>

          {canScrollRight && (
            <button
              type="button"
              className="video-explorer-carousel-arrow video-explorer-carousel-arrow-right"
              onClick={() => scrollSeriesCarousel(rowKey, 1)}
              aria-label={`Scroll ${title} right`}
            >
              <span className="material-icons">chevron_right</span>
            </button>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="video-explorer">
      <div className="card video-explorer-card">
        {error && (
          <div className="video-explorer-error">
            <span className="material-icons">error_outline</span>
            <span>{error}</span>
          </div>
        )}

        <div className="video-explorer-libraries">
          <div className="video-library-picker-header">
            <button
              type="button"
              className="video-library-picker-toggle"
              onClick={() => {
                if (libraries.length > 0 && !isLoadingLibraries) {
                  setIsLibraryPickerOpen(prev => !prev);
                }
              }}
              aria-expanded={libraries.length > 0 && !isLoadingLibraries ? isLibraryPickerOpen : true}
              aria-controls="video-series-library-grid"
              disabled={libraries.length === 0 || isLoadingLibraries}
              title={libraries.length === 0 ? 'No libraries available' : 'Toggle library selection'}
            >
              <span className="material-icons">
                {isLibraryPickerOpen ? 'expand_less' : 'expand_more'}
              </span>
              <span className="video-library-picker-title">{selectedLibraryName}</span>
            </button>

            <span className="video-library-picker-spacer" />

            {selectedLibraryId != null && (
              <button
                type="button"
                className={`video-explorer-star-btn ${defaultLibraryId === selectedLibraryId ? 'active' : ''}`}
                onClick={() => setAsDefaultLibrary(selectedLibraryId)}
                aria-label={defaultLibraryId === selectedLibraryId ? 'Default folder' : 'Set as default folder'}
                title={defaultLibraryId === selectedLibraryId ? 'Default folder' : 'Set as default'}
              >
                <span className="material-icons">
                  {defaultLibraryId === selectedLibraryId ? 'star' : 'star_border'}
                </span>
              </button>
            )}
          </div>

          {isLoadingLibraries ? (
            <div className="video-explorer-loading">Loading libraries…</div>
          ) : libraries.length === 0 ? (
            <div className="video-explorer-empty">No video libraries configured.</div>
          ) : isLibraryPickerOpen ? (
            <div className="video-explorer-library-grid" id="video-series-library-grid">
              {libraries.map((lib) => {
                const isSelected = selectedLibraryId === lib.id;
                const isDefault = defaultLibraryId === lib.id;

                return (
                  <button
                    key={lib.id}
                    type="button"
                    className={`video-explorer-library-btn ${isSelected ? 'selected' : ''}`}
                    onClick={() => {
                      setSelectedLibraryId(lib.id);
                      const next = new URLSearchParams(searchParams);
                      next.set(LIBRARY_ID_QUERY_KEY, String(lib.id));
                      // Switching libraries invalidates any selected series/season.
                      next.delete(SERIES_ID_QUERY_KEY);
                      next.delete(SEASON_ID_QUERY_KEY);
                      next.delete(SERIES_PATH_QUERY_KEY);
                      next.delete(SEASON_PATH_QUERY_KEY);
                      setSearchParams(next);
                    }}
                    title={lib.path}
                  >
                    <span className="video-explorer-library-name">{lib.name}</span>
                    <span className="video-explorer-library-spacer" />
                    <span
                      role="button"
                      tabIndex={0}
                      className={`video-explorer-star-btn ${isDefault ? 'active' : ''}`}
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        setAsDefaultLibrary(lib.id);
                      }}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault();
                          e.stopPropagation();
                          setAsDefaultLibrary(lib.id);
                        }
                      }}
                      aria-label={isDefault ? 'Default folder' : 'Set as default folder'}
                      title={isDefault ? 'Default folder' : 'Set as default'}
                    >
                      <span className="material-icons">{isDefault ? 'star' : 'star_border'}</span>
                    </span>
                  </button>
                );
              })}
            </div>
          ) : null}
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
              {renderSeriesCarouselRow(RECENT_SERIES_ROW_KEY, 'Recently Watched', recentSeries)}

              {seriesTags.map((tag) => {
                const items = seriesByTag.get(tag) || [];
                return renderSeriesCarouselRow(tag, tag, items);
              })}
            </div>
          )}
        </div>
      )}

      {selectedSeries && (
        <VideoSeriesModal
          series={selectedSeries}
          selectedSeason={selectedSeason}
          onSelectSeason={selectSeason}
          onClose={closeModal}
          onError={setError}
        />
      )}
    </div>
  );
}

export default VideoSeries;
