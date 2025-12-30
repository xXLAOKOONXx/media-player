import { useEffect, useMemo, useState } from 'react';
import './VideoExplorer.css';

const API_BASE_URL = '';

export interface VideoDetailsModalVideo {
  name: string;
  path: string;
  title?: string;
  artist?: string;
  director?: string;
  series?: string;
  duration?: number;
  start_time_in_ms?: number;
  end_time_in_ms?: number;
  tags?: string[];
  description?: string;
  thumbnail_url?: string;
  has_thumbnail?: boolean;
  media_id?: string;
  user_rating?: number;
}

interface VideoDetailsModalProps {
  video: VideoDetailsModalVideo;
  onClose: () => void;
  onPlay?: (video: VideoDetailsModalVideo) => void;
  isPlayDisabled?: boolean;
  playLabel?: string;
  onVideoUpdated?: (video: VideoDetailsModalVideo) => void;
}

const formatDuration = (seconds?: number) => {
  if (seconds == null || Number.isNaN(seconds)) return '—';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
};

const getTitle = (video: VideoDetailsModalVideo) => (video.title || video.name || 'Untitled').trim();

const getCreatorText = (video: VideoDetailsModalVideo) => {
  const artist = (video.artist || '').trim();
  if (artist) return artist;
  const director = (video.director || '').trim();
  return director;
};

const getThumbnailSrc = (video: VideoDetailsModalVideo) => {
  if (video.media_id) {
    return `${API_BASE_URL}/api/video/thumbnail/by-id/${encodeURIComponent(video.media_id)}`;
  }
  if (video.thumbnail_url) return video.thumbnail_url;
  return null;
};

const clampRating = (value: number) => {
  if (value < 0) return 0;
  if (value > 10) return 10;
  return value;
};

const clampMs = (value: number) => {
  if (value < 0) return 0;
  return Math.trunc(value);
};

const normalizeTags = (tags: string[]) => {
  const out: string[] = [];
  const seen = new Set<string>();
  for (const t of tags) {
    const trimmed = (t || '').trim();
    if (!trimmed) continue;
    const key = trimmed.toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(trimmed);
  }
  return out;
};

export default function VideoDetailsModal({
  video,
  onClose,
  onPlay,
  isPlayDisabled,
  playLabel,
  onVideoUpdated,
}: VideoDetailsModalProps) {
  const [isCoverBroken, setIsCoverBroken] = useState(false);

  const [ratingText, setRatingText] = useState('');
  const [musicStartText, setMusicStartText] = useState('');
  const [musicEndText, setMusicEndText] = useState('');
  const [editTags, setEditTags] = useState<string[]>([]);
  const [newTagText, setNewTagText] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [onClose]);

  useEffect(() => {
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = prevOverflow;
    };
  }, []);

  useEffect(() => {
    setIsCoverBroken(false);
    setSaveError(null);
    const r = video.user_rating;
    setRatingText(r == null || Number.isNaN(r) ? '' : String(r));
    const s = video.start_time_in_ms;
    setMusicStartText(s == null || Number.isNaN(s) ? '' : String(Math.trunc(s)));
    const e = video.end_time_in_ms;
    setMusicEndText(e == null || Number.isNaN(e) ? '' : String(Math.trunc(e)));
    setEditTags(Array.isArray(video.tags) ? normalizeTags(video.tags) : []);
    setNewTagText('');
  }, [video]);

  const title = useMemo(() => getTitle(video), [video]);
  const creator = useMemo(() => getCreatorText(video), [video]);
  const coverSrc = useMemo(() => getThumbnailSrc(video), [video]);
  const showCover = !!coverSrc && !isCoverBroken;

  const canSave = !!video.media_id && !isSaving;

  const addTag = () => {
    const t = newTagText.trim();
    if (!t) return;
    setEditTags((prev) => normalizeTags([...prev, t]));
    setNewTagText('');
  };

  const removeTag = (tag: string) => {
    setEditTags((prev) => prev.filter((t) => t.toLowerCase() !== tag.toLowerCase()));
  };

  const saveUserMetadata = async () => {
    if (!video.media_id) {
      setSaveError('Missing media_id');
      return;
    }

    setIsSaving(true);
    setSaveError(null);

    let rating: number | null = null;
    const trimmed = ratingText.trim();
    if (trimmed) {
      const parsed = Number(trimmed);
      if (Number.isFinite(parsed)) {
        rating = clampRating(parsed);
      } else {
        setIsSaving(false);
        setSaveError('Rating must be a number between 0 and 10');
        return;
      }
    }

    const normalizedTags = normalizeTags(editTags);

    let startMs: number | null = null;
    let endMs: number | null = null;

    const startTrimmed = musicStartText.trim();
    if (startTrimmed) {
      const parsed = Number(startTrimmed);
      if (!Number.isFinite(parsed)) {
        setIsSaving(false);
        setSaveError('music_start must be a non-negative number (milliseconds)');
        return;
      }
      startMs = clampMs(parsed);
    }

    const endTrimmed = musicEndText.trim();
    if (endTrimmed) {
      const parsed = Number(endTrimmed);
      if (!Number.isFinite(parsed)) {
        setIsSaving(false);
        setSaveError('music_end must be a non-negative number (milliseconds)');
        return;
      }
      endMs = clampMs(parsed);
    }

    if (startMs != null && endMs != null && startMs >= endMs) {
      setIsSaving(false);
      setSaveError('music_start must be less than music_end');
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/video/metadata/user`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          media_id: video.media_id,
          user_rating: rating,
          tags: normalizedTags,
          start_time_in_ms: startMs,
          end_time_in_ms: endMs,
        }),
      });

      if (response.status === 401) {
        setSaveError('Login required');
        return;
      }
      if (!response.ok) {
        const text = await response.text();
        setSaveError(text || 'Failed to save');
        return;
      }

      const updated: VideoDetailsModalVideo = {
        ...video,
        user_rating: rating == null ? undefined : rating,
        tags: normalizedTags,
        start_time_in_ms: startMs == null ? undefined : startMs,
        end_time_in_ms: endMs == null ? undefined : endMs,
      };
      onVideoUpdated?.(updated);
    } catch {
      setSaveError('Failed to save');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div
      className="video-explorer-modal-overlay"
      role="dialog"
      aria-modal="true"
      onClick={onClose}
    >
      <div className="video-explorer-modal card" onClick={(e) => e.stopPropagation()}>
        <div className="video-explorer-modal-header">
          <h3>{title}</h3>
          <button
            type="button"
            className="video-explorer-modal-close"
            onClick={onClose}
            aria-label="Close"
          >
            <span className="material-icons">close</span>
          </button>
        </div>

        <div className="video-explorer-modal-body">
          <div className="video-explorer-modal-cover">
            {showCover ? (
              <img
                src={coverSrc as string}
                alt={title}
                loading="lazy"
                onError={() => setIsCoverBroken(true)}
              />
            ) : (
              <div className="video-explorer-modal-cover-placeholder" aria-hidden>
                <span className="material-icons">movie</span>
              </div>
            )}
          </div>

          <div className="video-explorer-modal-meta">
            {creator && (
              <div className="video-explorer-meta-row">
                <span className="material-icons">person</span>
                <span>{creator}</span>
              </div>
            )}
            {video.series && (
              <div className="video-explorer-meta-row">
                <span className="material-icons">collections</span>
                <span>{video.series}</span>
              </div>
            )}
            <div className="video-explorer-meta-row">
              <span className="material-icons">schedule</span>
              <span>{formatDuration(video.duration)}</span>
            </div>

            <div className="video-explorer-meta-row">
              <span className="material-icons">timer</span>
              <span className="video-explorer-inline-field">
                <label className="video-explorer-inline-label" htmlFor="video-music-start">
                  music_start
                </label>
                <input
                  id="video-music-start"
                  className="video-explorer-edit-input"
                  type="number"
                  min={0}
                  step={1}
                  value={musicStartText}
                  onChange={(e) => setMusicStartText(e.target.value)}
                  placeholder="ms"
                  title="Milliseconds (ms)"
                  disabled={!video.media_id || isSaving}
                />
              </span>
            </div>

            <div className="video-explorer-meta-row">
              <span className="material-icons">timer</span>
              <span className="video-explorer-inline-field">
                <label className="video-explorer-inline-label" htmlFor="video-music-end">
                  music_end
                </label>
                <input
                  id="video-music-end"
                  className="video-explorer-edit-input"
                  type="number"
                  min={0}
                  step={1}
                  value={musicEndText}
                  onChange={(e) => setMusicEndText(e.target.value)}
                  placeholder="ms"
                  title="Milliseconds (ms)"
                  disabled={!video.media_id || isSaving}
                />
              </span>
            </div>

            <div className="video-explorer-meta-row">
              <span className="material-icons">star</span>
              <span className="video-explorer-inline-field">
                <label className="video-explorer-inline-label" htmlFor="video-user-rating">
                  Rating
                </label>
                <input
                  id="video-user-rating"
                  className="video-explorer-edit-input"
                  type="number"
                  min={0}
                  max={10}
                  step={0.1}
                  value={ratingText}
                  onChange={(e) => setRatingText(e.target.value)}
                  placeholder="0–10"
                  disabled={!video.media_id || isSaving}
                />
              </span>
            </div>
          </div>

          {video.description && (
            <div className="video-explorer-description">
              <h4>Description</h4>
              <p>{video.description}</p>
            </div>
          )}

          <div className="video-explorer-tags">
            <h4>Tags</h4>
            {editTags.length > 0 ? (
              <div className="video-explorer-tag-list">
                {editTags.map((t) => (
                  <span key={t} className="video-explorer-tag">
                    <span>{t}</span>
                    <button
                      type="button"
                      className="video-explorer-tag-remove"
                      onClick={() => removeTag(t)}
                      disabled={!video.media_id || isSaving}
                      aria-label={`Remove tag ${t}`}
                      title={`Remove ${t}`}
                    >
                      <span className="material-icons">close</span>
                    </button>
                  </span>
                ))}
              </div>
            ) : (
              <div className="video-explorer-empty">No tags</div>
            )}

            <div className="video-explorer-tag-editor">
              <input
                className="video-explorer-edit-input"
                type="text"
                value={newTagText}
                onChange={(e) => setNewTagText(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    addTag();
                  }
                }}
                placeholder="Add tag"
                disabled={!video.media_id || isSaving}
              />
              <button
                type="button"
                className="btn btn-secondary"
                onClick={addTag}
                disabled={!video.media_id || isSaving || !newTagText.trim()}
              >
                Add
              </button>
            </div>
          </div>

          {saveError && <div className="video-explorer-modal-error">{saveError}</div>}

          <div className="video-explorer-actions">
            <button
              type="button"
              className="btn btn-secondary"
              onClick={saveUserMetadata}
              disabled={!canSave}
              title={!video.media_id ? 'Missing media_id' : isSaving ? 'Saving…' : 'Save rating and tags'}
            >
              <span className="material-icons">save</span>
              <span>{isSaving ? 'Saving…' : 'Save'}</span>
            </button>

            {onPlay && (
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => onPlay(video)}
                disabled={!!isPlayDisabled}
              >
                <span className="material-icons">play_arrow</span>
                <span>{playLabel || 'Play'}</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
