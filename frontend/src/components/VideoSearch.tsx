import { useEffect, useMemo, useState } from 'react';
import './VideoExplorer.css';
import './VideoSearch.css';
import VideoDetailsModal from './VideoDetailsModal';
import type { VideoDetailsModalVideo } from './VideoDetailsModal';
import VideoSeriesModal from './VideoSeriesModal';
import {
  getSeriesWatchedState,
  normalizeCoverSrc,
} from './videoSeriesShared';
import type { Series, Season } from './videoSeriesShared';

const API_BASE_URL = '';

interface VideoLibrary {
  id: number;
  name: string;
  path: string;
  recursive: boolean;
  storage_id?: number;
}

interface Film {
  name: string;
  path: string;
  size?: number;
  director?: string;
  artist?: string;
  title?: string;
  series?: string;
  duration?: number;
  start_time_in_ms?: number;
  end_time_in_ms?: number;
  tags?: string[];
  description?: string;
  thumbnail_url?: string;
  has_thumbnail?: boolean;
  media_id?: string;
  playcount?: number;
  last_played?: number | null;
  user_rating?: number;
  promotion_score?: number;
}

const CAROUSEL_TILE_HEIGHT_PX = 210;

const getFilmTitle = (film: Film) => (film.title || film.name || 'Untitled').trim();

const getFilmThumbnailSrc = (film: Film) => {
  if (film.has_thumbnail && film.media_id) {
    return `${API_BASE_URL}/api/video/thumbnail/by-id/${encodeURIComponent(film.media_id)}`;
  }
  if (film.thumbnail_url) return film.thumbnail_url;
  return null;
};

const normalize = (value: unknown) =>
  typeof value === 'string' ? value.trim().toLowerCase() : '';

const includesQuery = (value: unknown, query: string) => {
  const text = normalize(value);
  return !!text && text.includes(query);
};

const someIncludesQuery = (values: unknown, query: string) => {
  if (!Array.isArray(values)) return false;
  return values.some((v) => includesQuery(v, query));
};

// Match rank: 0 = title match, 1 = description match, 2 = other-field match, null = no match.
const getFilmMatchRank = (film: Film, query: string): number | null => {
  if (includesQuery(getFilmTitle(film), query)) return 0;
  if (includesQuery(film.description, query)) return 1;
  if (
    someIncludesQuery(film.tags, query) ||
    includesQuery(film.artist, query) ||
    includesQuery(film.director, query) ||
    includesQuery(film.series, query) ||
    includesQuery(film.name, query)
  ) {
    return 2;
  }
  return null;
};

const getSeriesMatchRank = (series: Series, query: string): number | null => {
  if (includesQuery(series.title, query)) return 0;
  if (someIncludesQuery(series.tags, query) || someIncludesQuery(series.artists, query)) return 2;
  return null;
};

type SeriesResult = { kind: 'series'; rank: number; series: Series };
type FilmResult = { kind: 'film'; rank: number; film: Film };
type SearchResult = SeriesResult | FilmResult;

function VideoSearch() {
  const [query, setQuery] = useState('');

  const [films, setFilms] = useState<Film[]>([]);
  const [seriesList, setSeriesList] = useState<Series[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [brokenThumbnails, setBrokenThumbnails] = useState<Set<string>>(new Set());
  const [thumbnailAspectRatios, setThumbnailAspectRatios] = useState<Map<string, number>>(new Map());

  const [selectedFilm, setSelectedFilm] = useState<Film | null>(null);
  const [isStartingPlayback, setIsStartingPlayback] = useState(false);

  const [selectedSeries, setSelectedSeries] = useState<Series | null>(null);
  const [selectedSeason, setSelectedSeason] = useState<Season | null>(null);

  // Load films + series from every configured library once on mount.
  useEffect(() => {
    let cancelled = false;

    const loadAll = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const librariesRes = await fetch(`${API_BASE_URL}/api/video/libraries`);
        const librariesData = await librariesRes.json();
        const libraries: VideoLibrary[] = Array.isArray(librariesData) ? librariesData : [];

        const allFilms: Film[] = [];
        const allSeries: Series[] = [];

        await Promise.all(
          libraries.map(async (lib) => {
            try {
              const [videosRes, seriesRes] = await Promise.all([
                fetch(`${API_BASE_URL}/api/video/libraries/${lib.id}/videos`),
                fetch(`${API_BASE_URL}/api/video/libraries/${lib.id}/series`),
              ]);

              const videosData = await videosRes.json();
              const seriesData = await seriesRes.json();

              if (Array.isArray(videosData)) {
                for (const v of videosData) {
                  // A "Film" is a standalone video that is not part of a series.
                  if (v && typeof v === 'object' && !(typeof v.series === 'string' && v.series.trim())) {
                    allFilms.push(v as Film);
                  }
                }
              }
              if (Array.isArray(seriesData)) {
                for (const s of seriesData) {
                  if (s && typeof s === 'object') allSeries.push(s as Series);
                }
              }
            } catch {
              // Ignore per-library failures so a single bad library doesn't break search.
            }
          }),
        );

        if (cancelled) return;
        setFilms(allFilms);
        setSeriesList(allSeries);
      } catch {
        if (!cancelled) setError('Failed to load videos for search');
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    };

    loadAll();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setSelectedFilm(null);
        setSelectedSeries(null);
        setSelectedSeason(null);
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, []);

  const results = useMemo<SearchResult[]>(() => {
    const q = normalize(query);
    if (!q) return [];

    const items: SearchResult[] = [];

    for (const s of seriesList) {
      const rank = getSeriesMatchRank(s, q);
      if (rank != null) items.push({ kind: 'series', rank, series: s });
    }
    for (const f of films) {
      const rank = getFilmMatchRank(f, q);
      if (rank != null) items.push({ kind: 'film', rank, film: f });
    }

    // Series first, then by match rank (title, description, other), then alphabetically.
    const kindRank = (item: SearchResult) => (item.kind === 'series' ? 0 : 1);
    const titleOf = (item: SearchResult) =>
      item.kind === 'series' ? (item.series.title || '').trim() : getFilmTitle(item.film);
    const idOf = (item: SearchResult) =>
      item.kind === 'series'
        ? item.series.id || item.series.full_path || ''
        : item.film.media_id || item.film.path || '';

    return items.sort((a, b) => {
      if (kindRank(a) !== kindRank(b)) return kindRank(a) - kindRank(b);
      if (a.rank !== b.rank) return a.rank - b.rank;
      const byTitle = titleOf(a).localeCompare(titleOf(b));
      if (byTitle) return byTitle;
      return idOf(a).localeCompare(idOf(b));
    });
  }, [query, films, seriesList]);

  const getCardWidthPx = (key: string) => {
    const ratio = thumbnailAspectRatios.get(key) || (16 / 9);
    const safeRatio = Number.isFinite(ratio) && ratio > 0 ? ratio : (16 / 9);
    return Math.max(1, Math.round(CAROUSEL_TILE_HEIGHT_PX * safeRatio));
  };

  const registerAspectRatio = (key: string, e: React.SyntheticEvent<HTMLImageElement>) => {
    const img = e.currentTarget;
    const w = img.naturalWidth;
    const h = img.naturalHeight;
    if (!w || !h) return;
    const ratio = w / h;
    if (!Number.isFinite(ratio) || ratio <= 0) return;
    setThumbnailAspectRatios((prev) => {
      if (prev.get(key) === ratio) return prev;
      const next = new Map(prev);
      next.set(key, ratio);
      return next;
    });
  };

  const registerBroken = (key: string) => {
    setBrokenThumbnails((prev) => {
      const next = new Set(prev);
      next.add(key);
      return next;
    });
  };

  const applyUserMetadataUpdate = (updated: VideoDetailsModalVideo) => {
    if (!updated.media_id) return;
    setFilms((prev) =>
      prev.map((f) =>
        f.media_id === updated.media_id
          ? {
              ...f,
              user_rating: updated.user_rating,
              tags: updated.tags,
              start_time_in_ms: updated.start_time_in_ms,
              end_time_in_ms: updated.end_time_in_ms,
            }
          : f,
      ),
    );
    setSelectedFilm((prev) =>
      prev && prev.media_id === updated.media_id
        ? {
            ...prev,
            user_rating: updated.user_rating,
            tags: updated.tags,
            start_time_in_ms: updated.start_time_in_ms,
            end_time_in_ms: updated.end_time_in_ms,
          }
        : prev,
    );
  };

  const startFilmPlayback = async (film: VideoDetailsModalVideo) => {
    setIsStartingPlayback(true);
    try {
      if (!film.media_id) {
        setError('Missing media_id for selected video');
        return;
      }
      const res = await fetch(`${API_BASE_URL}/api/video/playback/play-video`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ media_id: film.media_id }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => null);
        setError(data?.error || 'Failed to start playback');
        return;
      }
    } catch {
      setError('Failed to start playback');
    } finally {
      setIsStartingPlayback(false);
    }
  };

  const openSeries = (series: Series) => {
    setSelectedSeries(series);
    setSelectedSeason(null);
  };

  const closeSeries = () => {
    setSelectedSeries(null);
    setSelectedSeason(null);
  };

  const renderSeriesCard = (series: Series) => {
    const cover = normalizeCoverSrc(series.cover);
    const showCover = !!cover;
    const seriesTitle = (series.title || 'Untitled').trim();
    const watchedState = getSeriesWatchedState(series);
    const key = series.id || series.full_path || seriesTitle;
    const cardWidth = getCardWidthPx(key);

    return (
      <button
        key={`series-${key}`}
        type="button"
        className="video-series-tile video-explorer-thumb"
        onClick={() => openSeries(series)}
        title={seriesTitle}
        style={{ width: `${cardWidth}px` }}
      >
        <div className="video-explorer-thumb-image video-series-tile-image">
          {showCover ? (
            <img
              src={cover as string}
              alt={seriesTitle}
              loading="lazy"
              onLoad={(e) => registerAspectRatio(key, e)}
              onError={() => registerBroken(key)}
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
  };

  const renderFilmCard = (film: Film) => {
    const thumb = getFilmThumbnailSrc(film);
    const title = getFilmTitle(film);
    const key = film.media_id || film.path || title;
    const showImage = !!thumb && !brokenThumbnails.has(key);
    const cardWidth = getCardWidthPx(key);
    const isWatched = (film.playcount ?? 0) > 0;

    return (
      <button
        key={`film-${key}`}
        type="button"
        className="video-explorer-thumb"
        onClick={() => setSelectedFilm(film)}
        title={title}
        style={{ width: `${cardWidth}px` }}
      >
        <div className="video-explorer-thumb-image" style={{ height: `${CAROUSEL_TILE_HEIGHT_PX}px` }}>
          {showImage ? (
            <img
              src={thumb as string}
              alt={title}
              loading="lazy"
              onLoad={(e) => registerAspectRatio(key, e)}
              onError={() => registerBroken(key)}
            />
          ) : null}
          {!showImage && (
            <div className="video-explorer-thumb-placeholder">
              <span className="material-icons">movie</span>
            </div>
          )}
          {isWatched && (
            <div className="video-explorer-thumb-watched" aria-hidden title="Watched">
              <span className="material-icons">visibility</span>
            </div>
          )}
          <div className="video-explorer-thumb-title" aria-hidden>
            {title}
          </div>
        </div>
      </button>
    );
  };

  const hasQuery = normalize(query).length > 0;

  return (
    <div className="video-explorer video-search">
      <div className="card video-explorer-card">
        {error && (
          <div className="video-explorer-error">
            <span className="material-icons">error_outline</span>
            <span>{error}</span>
          </div>
        )}

        <div className="video-search-input-row">
          <span className="material-icons">search</span>
          <input
            className="video-search-input"
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search series and films…"
            aria-label="Search series and films"
            autoFocus
          />
          {query && (
            <button
              type="button"
              className="video-search-clear"
              onClick={() => setQuery('')}
              aria-label="Clear search"
              title="Clear search"
            >
              <span className="material-icons">close</span>
            </button>
          )}
        </div>

        {isLoading && <div className="video-explorer-loading">Loading library…</div>}
      </div>

      {!isLoading && (
        <div className="video-explorer-browse">
          {!hasQuery ? (
            <div className="card">
              <div className="video-explorer-empty">Type to search for series and films.</div>
            </div>
          ) : results.length === 0 ? (
            <div className="card">
              <div className="video-explorer-empty">No series or films match “{query.trim()}”.</div>
            </div>
          ) : (
            <div className="card">
              <div className="video-search-results">
                {results.map((item) =>
                  item.kind === 'series' ? renderSeriesCard(item.series) : renderFilmCard(item.film),
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {selectedFilm && (
        <VideoDetailsModal
          video={selectedFilm}
          onClose={() => setSelectedFilm(null)}
          onPlay={(film) => startFilmPlayback(film)}
          isPlayDisabled={isStartingPlayback}
          playLabel={isStartingPlayback ? 'Starting…' : 'Play'}
          onVideoUpdated={(updatedVideo) => applyUserMetadataUpdate(updatedVideo)}
        />
      )}

      {selectedSeries && (
        <VideoSeriesModal
          series={selectedSeries}
          selectedSeason={selectedSeason}
          onSelectSeason={(season) => setSelectedSeason(season)}
          onClose={closeSeries}
          onError={setError}
        />
      )}
    </div>
  );
}

export default VideoSearch;
