const API_BASE_URL = '';

export interface Video {
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
  premiere_date?: string;
  playcount?: number;
  last_played?: number | null;
  promotion_score?: number;
}

export interface Season {
  id?: string;
  full_path: string;
  title: string;
  user_rating?: number | null;
  tags?: string[];
  artists?: string[];
  cover?: string | null;
  index_number?: number | null;
  videos: Video[];
}

export interface Series {
  id?: string;
  full_path: string;
  title: string;
  user_rating?: number | null;
  tags?: string[];
  artists?: string[];
  cover?: string | null;
  seasons: Season[];
  videos: Video[];
}

export const CAROUSEL_TILE_HEIGHT_PX = 210;

export const getVideoTitle = (video: Video) => (video.title || video.name || 'Untitled').trim();

export const getThumbnailSrc = (video: Video) => {
  if (video.has_thumbnail && video.media_id) {
    return `${API_BASE_URL}/api/video/thumbnail/by-id/${encodeURIComponent(video.media_id)}`;
  }
  if (video.thumbnail_url) return video.thumbnail_url;
  return null;
};

export const getPremiereDateKey = (video: Video) => {
  const raw = typeof video.premiere_date === 'string' ? video.premiere_date.trim() : '';
  if (!raw) return null;

  // Expect YYYY-MM-DD from NFO parsing; interpret as UTC midnight to avoid timezone shifts.
  const ms = Date.parse(`${raw}T00:00:00Z`);
  if (!Number.isFinite(ms)) return null;
  return ms;
};

export const normalizeCoverSrc = (cover?: string | null) => {
  if (!cover) return null;
  // API-relative covers (e.g. /api/video/thumbnail/by-id/...) should stay relative to API_BASE_URL
  if (cover.startsWith('/')) return `${API_BASE_URL}${cover}`;
  return cover;
};

export const isVideoWatched = (video: Video) => (video.playcount ?? 0) > 0;

export const getSeasonWatchedState = (season: Season) => {
  const videos = Array.isArray(season.videos) ? season.videos : [];
  const total = videos.length;
  const watched = videos.filter(isVideoWatched).length;
  return {
    total,
    watched,
    isFullyWatched: total > 0 && watched === total,
    isStarted: watched > 0 && watched < total,
  };
};

export const getSeriesWatchedState = (series: Series) => {
  const all: Video[] = [];
  if (Array.isArray(series.videos)) all.push(...series.videos);
  if (Array.isArray(series.seasons)) {
    for (const season of series.seasons) {
      if (Array.isArray(season.videos)) all.push(...season.videos);
    }
  }
  const total = all.length;
  const watched = all.filter(isVideoWatched).length;
  return {
    total,
    watched,
    isFullyWatched: total > 0 && watched === total,
    isStarted: watched > 0 && watched < total,
  };
};
