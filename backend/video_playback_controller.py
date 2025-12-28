"""
Video Playback Controller
Handles video playback management (playlist, status tracking)
Actual video playback is done client-side in the browser
"""

import os
from pathlib import Path
import random
import copy
import logging

# Configure logging
logger = logging.getLogger('VideoPlaybackController')
if not logger.handlers:
    logger.setLevel(logging.INFO)


class VideoPlaybackController:
    """Controls video playback state and playlist management"""
    
    def __init__(self):
        self.current_playlist = []
        self.original_playlist = []  # Store original order for shuffle
        self.current_track_index = 0
        self.is_playing = False
        self.is_paused = False
        self.volume = 0.5
        self.current_position = 0  # Current playback position in seconds
        
        # Shuffle and repeat modes
        self.shuffle_enabled = False
        self.repeat_mode = 'none'  # 'none', 'all', 'one'
        
        # Track timing state
        self.track_custom_start = None  # Custom start time in track (seconds)
        self.track_custom_end = None  # Custom end time in track (seconds)
    
    def load_playlist(self, playlist_path, track_index=0):
        """Load a video playlist from an M3U file"""
        if not os.path.exists(playlist_path):
            logger.error(f"Playlist not found: {playlist_path}")
            return False
        
        playlist_dir = os.path.dirname(playlist_path)
        tracks = []
        
        try:
            with open(playlist_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Handle relative and absolute paths
                        if os.path.isabs(line):
                            track_path = line
                        else:
                            track_path = os.path.join(playlist_dir, line)
                        
                        if os.path.exists(track_path):
                            tracks.append({
                                'path': track_path,
                                'title': os.path.basename(track_path),
                                'start_time': None,
                                'end_time': None
                            })
        except Exception as e:
            logger.error(f"Error loading playlist {playlist_path}: {e}")
            return False
        
        if not tracks:
            logger.error(f"No valid tracks found in playlist: {playlist_path}")
            return False
        
        self.current_playlist = tracks
        self.original_playlist = copy.deepcopy(tracks)
        self.current_track_index = min(track_index, len(tracks) - 1)
        self.current_position = 0
        
        logger.info(f"Loaded playlist with {len(tracks)} videos")
        return True
    
    def add_tracks(self, track_paths):
        """Add tracks to the current playlist"""
        for path in track_paths:
            if os.path.exists(path):
                self.current_playlist.append({
                    'path': path,
                    'title': os.path.basename(path),
                    'start_time': None,
                    'end_time': None
                })
        
        if not self.original_playlist:
            self.original_playlist = copy.deepcopy(self.current_playlist)
        
        return True
    
    def play(self):
        """Start or resume playback"""
        if not self.current_playlist:
            logger.warning("Cannot play: no playlist loaded")
            return False
        
        self.is_playing = True
        self.is_paused = False
        logger.info(f"Playing video {self.current_track_index + 1}/{len(self.current_playlist)}")
        return True
    
    def pause(self):
        """Pause playback"""
        if self.is_playing and not self.is_paused:
            self.is_paused = True
            logger.info("Video paused")
            return True
        return False
    
    def stop(self):
        """Stop playback"""
        self.is_playing = False
        self.is_paused = False
        self.current_position = 0
        logger.info("Video stopped")
        return True
    
    def next_track(self):
        """Skip to next track"""
        if not self.current_playlist:
            return False
        
        if self.current_track_index < len(self.current_playlist) - 1:
            self.current_track_index += 1
            self.current_position = 0
            logger.info(f"Skipped to next video: {self.current_track_index + 1}/{len(self.current_playlist)}")
            return True
        elif self.repeat_mode == 'all':
            self.current_track_index = 0
            self.current_position = 0
            logger.info("Playlist ended, repeating from start")
            return True
        else:
            logger.info("Reached end of playlist")
            self.stop()
            return False
    
    def previous_track(self):
        """Skip to previous track"""
        if not self.current_playlist:
            return False
        
        if self.current_track_index > 0:
            self.current_track_index -= 1
            self.current_position = 0
            logger.info(f"Skipped to previous video: {self.current_track_index + 1}/{len(self.current_playlist)}")
            return True
        return False
    
    def set_volume(self, volume):
        """Set playback volume (0.0 to 1.0)"""
        self.volume = max(0.0, min(1.0, volume))
        logger.info(f"Volume set to {self.volume * 100:.0f}%")
        return True
    
    def seek(self, position):
        """Seek to a specific position in seconds"""
        self.current_position = max(0, position)
        logger.info(f"Seeked to position {position}s")
        return True
    
    def set_shuffle(self, enabled):
        """Enable or disable shuffle mode"""
        if enabled and not self.shuffle_enabled:
            # Enable shuffle
            self.shuffle_enabled = True
            current_track = self.get_current_track()
            
            # Shuffle the playlist
            remaining_tracks = [t for i, t in enumerate(self.current_playlist) 
                              if i != self.current_track_index]
            random.shuffle(remaining_tracks)
            
            # Reconstruct playlist with current track first
            if current_track:
                self.current_playlist = [current_track] + remaining_tracks
                self.current_track_index = 0
            else:
                self.current_playlist = remaining_tracks
            
            logger.info("Shuffle enabled")
        elif not enabled and self.shuffle_enabled:
            # Disable shuffle - restore original order
            self.shuffle_enabled = False
            current_track = self.get_current_track()
            
            self.current_playlist = copy.deepcopy(self.original_playlist)
            
            # Find current track in original playlist
            if current_track:
                for i, track in enumerate(self.current_playlist):
                    if track['path'] == current_track['path']:
                        self.current_track_index = i
                        break
            
            logger.info("Shuffle disabled")
        
        return True
    
    def set_repeat_mode(self, mode):
        """Set repeat mode: 'none', 'all', or 'one'"""
        if mode in ['none', 'all', 'one']:
            self.repeat_mode = mode
            logger.info(f"Repeat mode set to: {mode}")
            return True
        return False
    
    def update_track_times(self, track_index, start_time=None, end_time=None):
        """Update custom start/end times for a track"""
        if 0 <= track_index < len(self.current_playlist):
            self.current_playlist[track_index]['start_time'] = start_time
            self.current_playlist[track_index]['end_time'] = end_time
            
            # Also update in original playlist if it exists
            if track_index < len(self.original_playlist):
                self.original_playlist[track_index]['start_time'] = start_time
                self.original_playlist[track_index]['end_time'] = end_time
            
            logger.info(f"Updated track {track_index} times: start={start_time}, end={end_time}")
            return True
        return False
    
    def get_current_track(self):
        """Get the currently selected track"""
        if 0 <= self.current_track_index < len(self.current_playlist):
            return self.current_playlist[self.current_track_index]
        return None
    
    def get_next_track(self):
        """Get the next track that will play"""
        if not self.current_playlist:
            return None
        
        next_index = self.current_track_index + 1
        
        if next_index < len(self.current_playlist):
            return self.current_playlist[next_index]
        elif self.repeat_mode == 'all':
            return self.current_playlist[0]
        
        return None
    
    def get_status(self):
        """Get current playback status"""
        current_track = self.get_current_track()
        next_track = self.get_next_track()
        
        return {
            'is_playing': self.is_playing,
            'is_paused': self.is_paused,
            'current_track': current_track,
            'next_track': next_track,
            'current_track_index': self.current_track_index,
            'playlist_length': len(self.current_playlist),
            'volume': int(self.volume * 100),
            'shuffle': self.shuffle_enabled,
            'repeat_mode': self.repeat_mode,
            'current_position': self.current_position
        }
    
    def get_playlist(self):
        """Get the current playlist"""
        return self.current_playlist
