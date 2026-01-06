/**
 * Utility functions for playlist creation with weighting and ordering
 */

export type OccurrenceMode = 'once' | 'rating' | 'rating_squared';
export type OrderMode = 'current' | 'shuffle';

export interface MediaItem {
  media_id?: string;
  user_rating?: number;
  [key: string]: any;
}

/**
 * Shuffle an array in place using Fisher-Yates algorithm
 */
function shuffleArray<T>(array: T[]): T[] {
  const result = [...array];
  for (let i = result.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [result[i], result[j]] = [result[j], result[i]];
  }
  return result;
}

/**
 * Create a weighted playlist from selected media items
 * 
 * @param items - Array of media items (tracks or videos) with media_id and optional user_rating
 * @param occurrenceMode - How many times each item appears: 'once', 'rating', or 'rating_squared'
 * @param orderMode - Whether to keep current order or shuffle: 'current' or 'shuffle'
 * @returns Array of media_ids in the desired order
 */
export function createWeightedPlaylist(
  items: MediaItem[],
  occurrenceMode: OccurrenceMode,
  orderMode: OrderMode
): string[] {
  // Filter items to only those with media_id
  const validItems = items.filter(item => item.media_id);
  
  if (validItems.length === 0) {
    return [];
  }

  // Build the weighted playlist based on occurrence mode
  let mediaIds: string[] = [];

  switch (occurrenceMode) {
    case 'once':
      // Each item appears exactly once
      mediaIds = validItems.map(item => item.media_id!);
      break;

    case 'rating':
      // Each item appears N times where N = rating (rounded to nearest integer)
      // Items without rating appear once (rating = 0 means don't include)
      for (const item of validItems) {
        const rating = item.user_rating ?? 0;
        const count = Math.max(0, Math.round(rating));
        
        // Add the media_id 'count' times
        for (let i = 0; i < count; i++) {
          mediaIds.push(item.media_id!);
        }
      }
      break;

    case 'rating_squared':
      // Each item appears N times where N = rating²
      // Items without rating appear once (rating = 0 means don't include)
      for (const item of validItems) {
        const rating = item.user_rating ?? 0;
        const count = Math.max(0, Math.round(rating * rating));
        
        // Add the media_id 'count' times
        for (let i = 0; i < count; i++) {
          mediaIds.push(item.media_id!);
        }
      }
      break;
  }

  // Apply ordering
  if (orderMode === 'shuffle') {
    mediaIds = shuffleArray(mediaIds);
  }
  // 'current' order means we keep the order as built above

  return mediaIds;
}
