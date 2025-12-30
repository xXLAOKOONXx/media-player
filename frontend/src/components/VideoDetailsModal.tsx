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
  tags?: string[];
  description?: string;
  thumbnail_url?: string;
  has_thumbnail?: boolean;
  media_id?: string;
}

interface VideoDetailsModalProps {
  video: VideoDetailsModalVideo;
  onClose: () => void;
  onPlay?: (video: VideoDetailsModalVideo) => void;
  isPlayDisabled?: boolean;
  playLabel?: string;
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

export default function VideoDetailsModal({
  video,
  onClose,
  onPlay,
  isPlayDisabled,
  playLabel,
}: VideoDetailsModalProps) {
  const [isCoverBroken, setIsCoverBroken] = useState(false);

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

  const title = useMemo(() => getTitle(video), [video]);
  const creator = useMemo(() => getCreatorText(video), [video]);
  const coverSrc = useMemo(() => getThumbnailSrc(video), [video]);
  const showCover = !!coverSrc && !isCoverBroken;

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
          </div>

          {video.description && (
            <div className="video-explorer-description">
              <h4>Description</h4>
              <p>{video.description}</p>
            </div>
          )}

          {video.tags && video.tags.length > 0 && (
            <div className="video-explorer-tags">
              <h4>Tags</h4>
              <div className="video-explorer-tag-list">
                {video.tags.map((t) => (
                  <span key={t} className="video-explorer-tag">{t}</span>
                ))}
              </div>
            </div>
          )}

          {onPlay && (
            <div className="video-explorer-actions">
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => onPlay(video)}
                disabled={!!isPlayDisabled}
              >
                <span className="material-icons">play_arrow</span>
                <span>{playLabel || 'Play'}</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
