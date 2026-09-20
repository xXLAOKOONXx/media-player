import { useEffect, useMemo, useRef, useState } from 'react';
import './VideoExplorer.css';
import './VideoSeries.css';
import {
  CAROUSEL_TILE_HEIGHT_PX,
  getPremiereDateKey,
  getSeasonWatchedState,
  getThumbnailSrc,
  getVideoTitle,
  normalizeCoverSrc,
} from './videoSeriesShared';
import type { Season, Series, Video } from './videoSeriesShared';

const API_BASE_URL = '';

interface VideoSeriesModalProps {
  series: Series;
  selectedSeason: Season | null;
  onSelectSeason: (season: Season) => void;
  onClose: () => void;
  onError: (message: string | null) => void;
}

export default function VideoSeriesModal({
  series,
  selectedSeason,
  onSelectSeason,
  onClose,
  onError,
}: VideoSeriesModalProps) {
  const [brokenThumbnails, setBrokenThumbnails] = useState<Set<string>>(new Set());
  const [thumbnailAspectRatios, setThumbnailAspectRatios] = useState<Map<string, number>>(new Map());
  const [isAddingToQueue, setIsAddingToQueue] = useState(false);

  const episodesCarouselRef = useRef<HTMLDivElement | null>(null);
  const [episodesCanScroll, setEpisodesCanScroll] = useState({ canScrollLeft: false, canScrollRight: false });

  const setError = onError;

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
    } catch {
      setError('Failed to start playback');
    }
  };

  const sortEpisodeList = (videos: Video[]) => {
    const items = Array.isArray(videos) ? videos : [];
    const hasAnyIndex = items.some(v => typeof v.index_number === 'number' && Number.isFinite(v.index_number));
    return [...items].sort((a, b) => {
      const aTitle = getVideoTitle(a);
      const bTitle = getVideoTitle(b);

      if (hasAnyIndex) {
        const aIndex = typeof a.index_number === 'number' && Number.isFinite(a.index_number) ? a.index_number : Number.POSITIVE_INFINITY;
        const bIndex = typeof b.index_number === 'number' && Number.isFinite(b.index_number) ? b.index_number : Number.POSITIVE_INFINITY;
        if (aIndex !== bIndex) return aIndex - bIndex;
      }

      const aDate = getPremiereDateKey(a) ?? Number.POSITIVE_INFINITY;
      const bDate = getPremiereDateKey(b) ?? Number.POSITIVE_INFINITY;
      if (aDate !== bDate) return aDate - bDate;

      const byTitle = aTitle.localeCompare(bTitle);
      if (byTitle) return byTitle;
      return (a.path || '').localeCompare(b.path || '');
    });
  };

  const displayedVideos = useMemo(() => {
    const raw = selectedSeason ? selectedSeason.videos : series?.videos;
    const items = Array.isArray(raw) ? raw : [];
    return sortEpisodeList(items);
  }, [selectedSeason, series]);

  const updateEpisodesScrollState = () => {
    const el = episodesCarouselRef.current;
    if (!el) return;
    const canScrollLeft = el.scrollLeft > 1;
    const canScrollRight = el.scrollLeft + el.clientWidth < el.scrollWidth - 1;
    setEpisodesCanScroll(prev => {
      if (prev.canScrollLeft === canScrollLeft && prev.canScrollRight === canScrollRight) return prev;
      return { canScrollLeft, canScrollRight };
    });
  };

  useEffect(() => {
    const raf = window.requestAnimationFrame(() => updateEpisodesScrollState());
    return () => window.cancelAnimationFrame(raf);
  }, [displayedVideos.length, thumbnailAspectRatios]);

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

  const scrollEpisodesCarousel = (direction: -1 | 1) => {
    const el = episodesCarouselRef.current;
    if (!el) return;
    el.scrollBy({ left: direction * 420, behavior: 'smooth' });
    window.setTimeout(() => updateEpisodesScrollState(), 350);
  };

  const addVideosToQueue = async (
    mediaIds: string[],
    options?: { manageLoadingState?: boolean }
  ) => {
    const ids = (Array.isArray(mediaIds) ? mediaIds : []).filter((id): id is string => typeof id === 'string' && id.trim().length > 0);
    if (ids.length === 0) {
      setError('No playable videos to add to the queue');
      return;
    }

    const manageLoadingState = options?.manageLoadingState !== false;

    if (manageLoadingState) setIsAddingToQueue(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/video/playback/add-videos`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ media_ids: ids })
      });

      if (!res.ok) {
        const data = await res.json().catch(() => null);
        setError(data?.error || 'Failed to add videos to the queue');
      }
    } catch {
      setError('Failed to add videos to the queue');
    } finally {
      if (manageLoadingState) setIsAddingToQueue(false);
    }
  };

  const stopAndResetPlaybackModes = async () => {
    try {
      const stopRes = await fetch(`${API_BASE_URL}/api/video/playback/stop`, {
        method: 'POST'
      });
      if (!stopRes.ok) {
        setError('Failed to stop playback');
        return false;
      }
    } catch {
      setError('Failed to stop playback');
      return false;
    }

    try {
      const shuffleRes = await fetch(`${API_BASE_URL}/api/video/playback/shuffle`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: false })
      });
      if (!shuffleRes.ok) {
        setError('Failed to disable shuffle');
        return false;
      }
    } catch {
      setError('Failed to disable shuffle');
      return false;
    }

    try {
      const repeatRes = await fetch(`${API_BASE_URL}/api/video/playback/repeat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: 'none' })
      });
      if (!repeatRes.ok) {
        setError('Failed to set repeat mode');
        return false;
      }
    } catch {
      setError('Failed to set repeat mode');
      return false;
    }

    return true;
  };

  const continueWatching = async () => {
    if (!series) return;

    const groups: Array<{ key: string; seasonTitle: string; videos: Video[] }> = [];

    if (Array.isArray(series.seasons)) {
      for (const season of series.seasons) {
        const sorted = sortEpisodeList(Array.isArray(season.videos) ? season.videos : []);
        groups.push({ key: season.id || season.full_path, seasonTitle: season.title, videos: sorted });
      }
    }

    const seriesVideosSorted = sortEpisodeList(Array.isArray(series.videos) ? series.videos : []);
    if (seriesVideosSorted.length > 0) {
      groups.push({ key: '__series_videos__', seasonTitle: 'Videos', videos: seriesVideosSorted });
    }

    if (groups.length === 0) {
      setError('No videos found for this series');
      return;
    }

    type LastWatched = { groupKey: string; mediaId?: string; path?: string; lastPlayed: number };
    let last: LastWatched | null = null;

    for (const group of groups) {
      for (const v of group.videos) {
        const playcount = v.playcount ?? 0;
        const lastPlayed = v.last_played;
        if (!playcount || lastPlayed == null || !Number.isFinite(lastPlayed)) continue;
        if (!last || lastPlayed > last.lastPlayed) {
          last = { groupKey: group.key, mediaId: v.media_id, path: v.path, lastPlayed };
        }
      }
    }

    const targetGroup = last ? groups.find(g => g.key === last.groupKey) : groups[0];
    if (!targetGroup) {
      setError('Unable to determine the next episode');
      return;
    }

    const findIndex = () => {
      if (!last) return -1;
      return targetGroup.videos.findIndex(v => {
        if (last.mediaId && v.media_id) return v.media_id === last.mediaId;
        if (last.path && v.path) return v.path === last.path;
        return false;
      });
    };

    const lastIdx = findIndex();
    const nextIdx = lastIdx + 1;
    const toQueue = nextIdx >= 0 ? targetGroup.videos.slice(nextIdx) : targetGroup.videos;

    const mediaIds = toQueue.map(v => v.media_id).filter((id): id is string => typeof id === 'string' && id.trim().length > 0);

    if (mediaIds.length === 0) {
      setError('No next episodes available to queue');
      return;
    }

    setIsAddingToQueue(true);
    try {
      const ok = await stopAndResetPlaybackModes();
      if (!ok) return;

      await addVideosToQueue(mediaIds, { manageLoadingState: false });
    } finally {
      setIsAddingToQueue(false);
    }
  };

  const playRandomFromDisplayed = async (unseenOnly: boolean) => {
    const getSeriesWidePool = () => {
      if (!series) return [];

      const all: Video[] = [];
      if (Array.isArray(series.videos)) all.push(...series.videos);
      if (Array.isArray(series.seasons)) {
        for (const season of series.seasons) {
          if (Array.isArray(season.videos)) all.push(...season.videos);
        }
      }

      // Avoid duplicates if a video appears in multiple lists.
      const seen = new Set<string>();
      return all.filter(v => {
        const key = (v.media_id || v.path || '').trim();
        if (!key) return false;
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      });
    };

    const sourceVideos = getSeriesWidePool();
    const pool = sourceVideos.filter(v => {
      if (!v.media_id) return false;
      if (!unseenOnly) return true;
      return (v.playcount ?? 0) === 0;
    });

    if (pool.length === 0) {
      setError(unseenOnly ? 'No unseen episodes found.' : 'No episodes found.');
      return;
    }

    const pick = pool[Math.floor(Math.random() * pool.length)];
    if (!pick?.media_id) {
      setError('Missing media_id for selected video');
      return;
    }
    await addVideosToQueue([pick.media_id]);
  };

  const renderVideoCarousel = (videos: Video[]) => {
    if (videos.length === 0) return <div className="video-explorer-empty">No videos found.</div>;

    return (
      <div className="video-explorer-carousel-container video-series-episodes-carousel-container">
        {episodesCanScroll.canScrollLeft && (
          <button
            type="button"
            className="video-explorer-carousel-arrow video-explorer-carousel-arrow-left"
            onClick={() => scrollEpisodesCarousel(-1)}
            aria-label="Scroll episodes left"
          >
            <span className="material-icons">chevron_left</span>
          </button>
        )}

        <div
          className="video-explorer-carousel"
          onWheel={handleCarouselWheel}
          onScroll={updateEpisodesScrollState}
          ref={(el) => {
            episodesCarouselRef.current = el;
            if (el) window.requestAnimationFrame(() => updateEpisodesScrollState());
          }}
        >
          {videos.map((v) => {
            const title = getVideoTitle(v);
            const thumb = getThumbnailSrc(v);
            const brokenKey = v.media_id || v.path || title;
            const showImage = !!thumb && !brokenThumbnails.has(brokenKey);
            const cardWidth = getCardWidthPx(brokenKey);
            const isWatched = (v.playcount ?? 0) > 0;

            return (
              <button
                key={v.media_id || v.path || title}
                type="button"
                className="video-explorer-thumb"
                onClick={() => startPlayback(v)}
                title={title}
                style={{ width: `${cardWidth}px` }}
              >
                <div className="video-explorer-thumb-image" style={{ height: `${CAROUSEL_TILE_HEIGHT_PX}px` }}>
                  {showImage ? (
                    <img
                      src={thumb as string}
                      alt={title}
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
          })}
        </div>

        {episodesCanScroll.canScrollRight && (
          <button
            type="button"
            className="video-explorer-carousel-arrow video-explorer-carousel-arrow-right"
            onClick={() => scrollEpisodesCarousel(1)}
            aria-label="Scroll episodes right"
          >
            <span className="material-icons">chevron_right</span>
          </button>
        )}
      </div>
    );
  };

  return (
    <div
      className="video-explorer-modal-overlay"
      role="dialog"
      aria-modal="true"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="card video-explorer-modal">
        <div className="video-explorer-modal-header">
          <h3>{series.title}</h3>
          <button type="button" className="video-explorer-modal-close" onClick={onClose} aria-label="Close">
            <span className="material-icons">close</span>
          </button>
        </div>

        <div className="video-explorer-modal-body">
          {(() => {
            const cover = normalizeCoverSrc(series.cover);
            if (cover) {
              return (
                <div className="video-explorer-modal-cover">
                  <img src={cover} alt={series.title} />
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

          {Array.isArray(series.seasons) && series.seasons.length > 0 && (
            <div className="video-series-seasons">
              <h4>Seasons</h4>
              <div className="video-series-season-buttons">
                {series.seasons.map((se) => {
                  const isSelected =
                    (selectedSeason?.id && se.id && selectedSeason.id === se.id) ||
                    (!selectedSeason?.id && selectedSeason?.full_path === se.full_path);
                  const watchedState = getSeasonWatchedState(se);

                  return (
                    <button
                      key={se.id || se.full_path}
                      type="button"
                      className={`btn ${isSelected ? 'active' : ''} ${watchedState.isFullyWatched ? 'video-series-season-complete' : ''}`}
                      onClick={() => onSelectSeason(se)}
                      title={watchedState.isFullyWatched ? 'Season fully watched' : undefined}
                    >
                      {se.title}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          <div className="video-series-episodes">
            <h4>{selectedSeason ? selectedSeason.title : 'Videos'}</h4>
            {renderVideoCarousel(displayedVideos)}
            <div className="video-series-episode-buttons">
              <button type="button" className="btn" onClick={continueWatching} disabled={isAddingToQueue}>
                Continue watching
              </button>
              <button
                type="button"
                className="btn"
                onClick={() => playRandomFromDisplayed(false)}
                disabled={isAddingToQueue}
                title="Adds one random episode/video from the entire series (all seasons) to the current queue."
              >
                Play Random
              </button>
              <button
                type="button"
                className="btn"
                onClick={() => playRandomFromDisplayed(true)}
                disabled={isAddingToQueue}
                title="Adds one random unseen episode/video (playcount == 0) from the entire series (all seasons) to the current queue."
              >
                Play Random Unseen
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
