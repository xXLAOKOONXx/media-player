import { useEffect, useMemo, useRef, useState } from 'react';
import './VideoExplorer.css';

const API_BASE_URL = '';

interface VideoLibrary {
  id: number;
  name: string;
  path: string;
  recursive: boolean;
  storage_id?: number;
}

interface Video {
  name: string;
  path: string;
  size?: number;
  director?: string;
  artist?: string;
  title?: string;
  series?: string;
  duration?: number;
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

const DEFAULT_LIBRARY_STORAGE_KEY = 'videoExplorer.defaultLibraryId';
const DAILY_SUGGESTIONS_ROW_KEY = '__daily_suggestions__';

const formatDuration = (seconds?: number) => {
  if (seconds == null || Number.isNaN(seconds)) return '—';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
};

const getTitle = (video: Video) => (video.title || video.name || 'Untitled').trim();

const getCreatorText = (video: Video) => {
  const artist = (video.artist || '').trim();
  if (artist) return artist;
  const director = (video.director || '').trim();
  return director;
};

const getThumbnailSrc = (video: Video) => {
  if (video.has_thumbnail && video.media_id) {
    return `${API_BASE_URL}/api/video/thumbnail/by-id/${encodeURIComponent(video.media_id)}`;
  }
  if (video.thumbnail_url) return video.thumbnail_url;
  return null;
};

function VideoExplorer() {
  const [libraries, setLibraries] = useState<VideoLibrary[]>([]);
  const [selectedLibraryId, setSelectedLibraryId] = useState<number | null>(null);
  const [defaultLibraryId, setDefaultLibraryId] = useState<number | null>(null);

  const [isLibraryPickerOpen, setIsLibraryPickerOpen] = useState(false);

  const [videos, setVideos] = useState<Video[]>([]);
  const [isLoadingLibraries, setIsLoadingLibraries] = useState(false);
  const [isLoadingVideos, setIsLoadingVideos] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [selectedVideo, setSelectedVideo] = useState<Video | null>(null);
  const [isStartingPlayback, setIsStartingPlayback] = useState(false);

  const [brokenThumbnails, setBrokenThumbnails] = useState<Set<string>>(new Set());
  const [thumbnailAspectRatios, setThumbnailAspectRatios] = useState<Map<string, number>>(new Map());

  const [carouselScrollState, setCarouselScrollState] = useState<
    Record<string, { canScrollLeft: boolean; canScrollRight: boolean }>
  >({});

  const CAROUSEL_TILE_HEIGHT_PX = 210; // +50% taller than previous 140px

  const carouselRefs = useRef<Record<string, HTMLDivElement | null>>({});

  const updateCarouselScrollState = (tag: string) => {
    const el = carouselRefs.current[tag];
    if (!el) return;
    const canScrollLeft = el.scrollLeft > 1;
    const canScrollRight = el.scrollLeft + el.clientWidth < el.scrollWidth - 1;
    setCarouselScrollState(prev => {
      const existing = prev[tag];
      if (
        existing &&
        existing.canScrollLeft === canScrollLeft &&
        existing.canScrollRight === canScrollRight
      ) {
        return prev;
      }
      return {
        ...prev,
        [tag]: { canScrollLeft, canScrollRight }
      };
    });
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

    // If a selection already exists and is still valid, keep it.
    if (selectedLibraryId && libraries.some(l => l.id === selectedLibraryId)) {
      return;
    }

    // Otherwise prefer stored default.
    if (defaultLibraryId && libraries.some(l => l.id === defaultLibraryId)) {
      setSelectedLibraryId(defaultLibraryId);
      return;
    }

    // Fallback to first library.
    setSelectedLibraryId(libraries[0].id);
  }, [libraries, defaultLibraryId, selectedLibraryId]);

  useEffect(() => {
    const loadVideos = async (libraryId: number) => {
      setIsLoadingVideos(true);
      setError(null);
      try {
        const response = await fetch(`${API_BASE_URL}/api/video/libraries/${libraryId}/videos`);
        const data = await response.json();
        setVideos(Array.isArray(data) ? data : []);
      } catch {
        setError('Failed to load videos for the selected library');
        setVideos([]);
      } finally {
        setIsLoadingVideos(false);
      }
    };

    if (selectedLibraryId != null) {
      setCarouselScrollState({});
      loadVideos(selectedLibraryId);
    } else {
      setVideos([]);
    }
  }, [selectedLibraryId]);

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setSelectedVideo(null);
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, []);

  useEffect(() => {
    // Prevent background page scrolling while the modal is open.
    if (!selectedVideo) return;
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = prevOverflow;
    };
  }, [selectedVideo]);

  const tags = useMemo(() => {
    const set = new Set<string>();
    for (const v of videos) {
      for (const t of v.tags || []) {
        const trimmed = (t || '').trim();
        if (trimmed) set.add(trimmed);
      }
    }
    // Randomize the order of tag rows (stable until `videos` changes).
    const arr = Array.from(set);
    for (let i = arr.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [arr[i], arr[j]] = [arr[j], arr[i]];
    }
    return arr;
  }, [videos]);

  const dailySuggestions = useMemo(() => {
    const sorted = [...videos];
    sorted.sort((a, b) => {
      const aScore = Number.isFinite(a.promotion_score as number) ? (a.promotion_score as number) : 0;
      const bScore = Number.isFinite(b.promotion_score as number) ? (b.promotion_score as number) : 0;
      if (bScore !== aScore) return bScore - aScore;
      const byTitle = getTitle(a).localeCompare(getTitle(b));
      if (byTitle) return byTitle;
      return (a.path || '').localeCompare(b.path || '');
    });
    return sorted.slice(0, 50);
  }, [videos]);

  const videosByTag = useMemo(() => {
    const map = new Map<string, Video[]>();
    for (const tag of tags) map.set(tag, []);

    for (const v of videos) {
      for (const t of v.tags || []) {
        const trimmed = (t || '').trim();
        if (!trimmed) continue;
        const bucket = map.get(trimmed);
        if (bucket) bucket.push(v);
      }
    }

    // Sort each carousel row by highest promotion score first.
    // Add a stable tie-breaker for deterministic ordering.
    for (const bucket of map.values()) {
      bucket.sort((a, b) => {
        const aScore = Number.isFinite(a.promotion_score as number) ? (a.promotion_score as number) : 0;
        const bScore = Number.isFinite(b.promotion_score as number) ? (b.promotion_score as number) : 0;
        if (bScore !== aScore) return bScore - aScore;
        const byTitle = getTitle(a).localeCompare(getTitle(b));
        if (byTitle) return byTitle;
        return (a.path || '').localeCompare(b.path || '');
      });
    }

    return map;
  }, [tags, videos]);

  const setAsDefaultLibrary = (libraryId: number) => {
    setDefaultLibraryId(libraryId);
    window.localStorage.setItem(DEFAULT_LIBRARY_STORAGE_KEY, String(libraryId));
  };

  const selectedLibraryName = useMemo(() => {
    const lib = libraries.find(l => l.id === selectedLibraryId);
    return (lib?.name || '').trim() || 'Select library';
  }, [libraries, selectedLibraryId]);

  const scrollCarousel = (tag: string, direction: -1 | 1) => {
    const el = carouselRefs.current[tag];
    if (!el) return;
    el.scrollBy({ left: direction * 420, behavior: 'smooth' });
    // In case the browser doesn't emit a scroll event for some reason,
    // update the button visibility shortly after the smooth scroll starts.
    window.setTimeout(() => updateCarouselScrollState(tag), 350);
  };

  useEffect(() => {
    // Thumbnails loading can change widths, which can change scrollability.
    // Recompute arrow visibility on the next frame.
    if (tags.length === 0 && dailySuggestions.length === 0) return;
    const raf = window.requestAnimationFrame(() => {
      if (dailySuggestions.length > 0) updateCarouselScrollState(DAILY_SUGGESTIONS_ROW_KEY);
      for (const tag of tags) updateCarouselScrollState(tag);
    });
    return () => window.cancelAnimationFrame(raf);
  }, [tags, dailySuggestions.length, thumbnailAspectRatios]);

  const handleCarouselWheel = (e: React.WheelEvent<HTMLDivElement>) => {
    // Prevent horizontal scrolling; navigation is via arrow buttons.
    // Keep vertical scroll working so the page can still be scrolled.
    if (e.shiftKey || Math.abs(e.deltaX) > 0) {
      e.preventDefault();
      e.stopPropagation();
    }
  };

  const getCardWidthPx = (key: string) => {
    const ratio = thumbnailAspectRatios.get(key) || (16 / 9);
    const safeRatio = Number.isFinite(ratio) && ratio > 0 ? ratio : (16 / 9);
    // Size the card to match the cover image aspect ratio (given the fixed row height).
    return Math.max(1, Math.round(CAROUSEL_TILE_HEIGHT_PX * safeRatio));
  };

  const startPlayback = async (video: Video) => {
    setIsStartingPlayback(true);
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

      setSelectedVideo(null);
    } catch {
      setError('Failed to start playback');
    } finally {
      setIsStartingPlayback(false);
    }
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
              aria-controls="video-explorer-library-grid"
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
            {isLoadingVideos && <div className="video-explorer-loading">Loading videos…</div>}
          </div>

          {!isLoadingVideos && tags.length === 0 ? (
            <div className="card">
              <div className="video-explorer-empty">No tagged videos found in this library.</div>
            </div>
          ) : (
            <>
              {dailySuggestions.length > 0 && (
                (() => {
                  const rowKey = DAILY_SUGGESTIONS_ROW_KEY;
                  const items = dailySuggestions;
                  const canScrollLeft = carouselScrollState[rowKey]?.canScrollLeft ?? false;
                  const canScrollRight = carouselScrollState[rowKey]?.canScrollRight ?? true;

                  return (
                    <div key={rowKey} className="video-explorer-carousel-section">
                      <div className="video-explorer-carousel-title">
                        <h4>Daily Suggestions</h4>
                      </div>

                      <div className="video-explorer-carousel-container">
                        {canScrollLeft && (
                          <button
                            type="button"
                            className="video-explorer-carousel-arrow video-explorer-carousel-arrow-left"
                            onClick={() => scrollCarousel(rowKey, -1)}
                            aria-label="Scroll Daily Suggestions left"
                          >
                            <span className="material-icons">chevron_left</span>
                          </button>
                        )}

                        <div
                          className="video-explorer-carousel"
                          onWheel={handleCarouselWheel}
                          onScroll={() => updateCarouselScrollState(rowKey)}
                          ref={(el) => {
                            carouselRefs.current[rowKey] = el;
                            if (el) {
                              window.requestAnimationFrame(() => updateCarouselScrollState(rowKey));
                            }
                          }}
                        >
                          {items.map((video) => {
                            const thumb = getThumbnailSrc(video);
                            const title = getTitle(video);
                            const brokenKey = video.media_id || video.path;
                            const showImage = !!thumb && !brokenThumbnails.has(brokenKey);
                            const cardWidth = getCardWidthPx(brokenKey);
                            const isWatched = (video.playcount ?? 0) > 0;

                            return (
                              <button
                                key={`${video.path}-${rowKey}`}
                                type="button"
                                className="video-explorer-thumb"
                                onClick={() => setSelectedVideo(video)}
                                title={title}
                                style={{ width: `${cardWidth}px` }}
                              >
                                <div className="video-explorer-thumb-image" style={{ height: `${CAROUSEL_TILE_HEIGHT_PX}px` }}>
                                  {showImage ? (
                                    <img
                                      src={thumb}
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

                        {canScrollRight && (
                          <button
                            type="button"
                            className="video-explorer-carousel-arrow video-explorer-carousel-arrow-right"
                            onClick={() => scrollCarousel(rowKey, 1)}
                            aria-label="Scroll Daily Suggestions right"
                          >
                            <span className="material-icons">chevron_right</span>
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })()
              )}

              {tags.map((tag) => {
                const items = videosByTag.get(tag) || [];
                if (items.length === 0) return null;

                const canScrollLeft = carouselScrollState[tag]?.canScrollLeft ?? false;
                const canScrollRight = carouselScrollState[tag]?.canScrollRight ?? true;

                return (
                  <div key={tag} className="video-explorer-carousel-section">
                    <div className="video-explorer-carousel-title">
                      <h4>{tag}</h4>
                    </div>

                    <div className="video-explorer-carousel-container">
                      {canScrollLeft && (
                        <button
                          type="button"
                          className="video-explorer-carousel-arrow video-explorer-carousel-arrow-left"
                          onClick={() => scrollCarousel(tag, -1)}
                          aria-label={`Scroll ${tag} left`}
                        >
                          <span className="material-icons">chevron_left</span>
                        </button>
                      )}

                      <div
                        className="video-explorer-carousel"
                        onWheel={handleCarouselWheel}
                        onScroll={() => updateCarouselScrollState(tag)}
                        ref={(el) => {
                          carouselRefs.current[tag] = el;
                          if (el) {
                            window.requestAnimationFrame(() => updateCarouselScrollState(tag));
                          }
                        }}
                      >
                        {items.map((video) => {
                      const thumb = getThumbnailSrc(video);
                      const title = getTitle(video);
                      const brokenKey = video.media_id || video.path;
                      const showImage = !!thumb && !brokenThumbnails.has(brokenKey);
                      const cardWidth = getCardWidthPx(brokenKey);
                      const isWatched = (video.playcount ?? 0) > 0;

                      return (
                        <button
                          key={`${video.path}-${tag}`}
                          type="button"
                          className="video-explorer-thumb"
                          onClick={() => setSelectedVideo(video)}
                          title={title}
                          style={{ width: `${cardWidth}px` }}
                        >
                          <div className="video-explorer-thumb-image" style={{ height: `${CAROUSEL_TILE_HEIGHT_PX}px` }}>
                            {showImage ? (
                              <img
                                src={thumb}
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
                                  // Remember broken thumbnails so we can show a placeholder.
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

                    {canScrollRight && (
                      <button
                        type="button"
                        className="video-explorer-carousel-arrow video-explorer-carousel-arrow-right"
                        onClick={() => scrollCarousel(tag, 1)}
                        aria-label={`Scroll ${tag} right`}
                      >
                        <span className="material-icons">chevron_right</span>
                      </button>
                    )}
                  </div>
                </div>
                );
              })}
            </>
          )}
        </div>
      )}

      {selectedVideo && (
        <div
          className="video-explorer-modal-overlay"
          role="dialog"
          aria-modal="true"
          onClick={() => setSelectedVideo(null)}
        >
          <div className="video-explorer-modal card" onClick={(e) => e.stopPropagation()}>
            <div className="video-explorer-modal-header">
              <h3>{getTitle(selectedVideo)}</h3>
              <button
                type="button"
                className="video-explorer-modal-close"
                onClick={() => setSelectedVideo(null)}
                aria-label="Close"
              >
                <span className="material-icons">close</span>
              </button>
            </div>

            <div className="video-explorer-modal-body">
              {(() => {
                const modalThumb = getThumbnailSrc(selectedVideo);
                const modalKey = selectedVideo.media_id || selectedVideo.path;
                const showModalImage = !!modalThumb && !brokenThumbnails.has(modalKey);
                const modalTitle = getTitle(selectedVideo);

                return (
                  <div className="video-explorer-modal-cover">
                    {showModalImage ? (
                      <img
                        src={modalThumb}
                        alt={modalTitle}
                        loading="lazy"
                        onError={() => {
                          setBrokenThumbnails(prev => {
                            const next = new Set(prev);
                            next.add(modalKey);
                            return next;
                          });
                        }}
                      />
                    ) : (
                      <div className="video-explorer-modal-cover-placeholder" aria-hidden>
                        <span className="material-icons">movie</span>
                      </div>
                    )}
                  </div>
                );
              })()}

              <div className="video-explorer-modal-meta">
                {getCreatorText(selectedVideo) && (
                  <div className="video-explorer-meta-row">
                    <span className="material-icons">person</span>
                    <span>{getCreatorText(selectedVideo)}</span>
                  </div>
                )}
                {selectedVideo.series && (
                  <div className="video-explorer-meta-row">
                    <span className="material-icons">collections</span>
                    <span>{selectedVideo.series}</span>
                  </div>
                )}
                <div className="video-explorer-meta-row">
                  <span className="material-icons">schedule</span>
                  <span>{formatDuration(selectedVideo.duration)}</span>
                </div>
              </div>

              {selectedVideo.description && (
                <div className="video-explorer-description">
                  <h4>Description</h4>
                  <p>{selectedVideo.description}</p>
                </div>
              )}

              {selectedVideo.tags && selectedVideo.tags.length > 0 && (
                <div className="video-explorer-tags">
                  <h4>Tags</h4>
                  <div className="video-explorer-tag-list">
                    {selectedVideo.tags.map((t) => (
                      <span key={t} className="video-explorer-tag">{t}</span>
                    ))}
                  </div>
                </div>
              )}

              <div className="video-explorer-actions">
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={() => startPlayback(selectedVideo)}
                  disabled={isStartingPlayback}
                >
                  <span className="material-icons">play_arrow</span>
                  <span>{isStartingPlayback ? 'Starting…' : 'Play'}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default VideoExplorer;
