"""
Playback Controller
Handles audio playback using pygame with crossfading support
"""

import pygame
import os
from pathlib import Path
from threading import Thread, Event
import time


class PlaybackController:
    """Controls audio playback with crossfading"""
    
    def __init__(self, crossfade_config=None):
        # Initialize pygame mixer
        try:
            pygame.mixer.init()
            self.audio_available = True
        except pygame.error as e:
            print(f"Warning: Audio initialization failed: {e}")
            print("Running in no-audio mode. Playback will be simulated.")
            self.audio_available = False
        
        self.current_playlist = []
        self.current_track_index = 0
        self.is_playing = False
        self.is_paused = False
        self.volume = 0.5
        
        # Crossfade configuration
        self.crossfade_config = crossfade_config or {
            'enabled': True,
            'duration_ms': 3000,  # 3 seconds default
            'fade_out_start_before_end_ms': 5000  # Start fading 5 seconds before track ends
        }
        
        # Crossfade state
        self.is_crossfading = False
        self.crossfade_start_time = None
        self.next_track_queued = False
        
        # Set initial volume if audio is available
        if self.audio_available:
            pygame.mixer.music.set_volume(self.volume)
        
        # Playback monitoring thread
        self.monitor_thread = None
        self.stop_monitoring = Event()
    
    def load_playlist(self, playlist_path):
        """Load a playlist from M3U file"""
        try:
            tracks = []
            playlist_dir = Path(playlist_path).parent
            
            with open(playlist_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            current_track = {}
            for line in lines:
                line = line.strip()
                
                if line.startswith('#EXTINF:'):
                    # Parse track info
                    parts = line[8:].split(',', 1)
                    if len(parts) == 2:
                        current_track['duration'] = parts[0]
                        current_track['title'] = parts[1]
                
                elif line and not line.startswith('#'):
                    # This is a file path
                    # Handle relative paths
                    if not os.path.isabs(line):
                        line = str(playlist_dir / line)
                    
                    current_track['path'] = line
                    if 'title' not in current_track:
                        current_track['title'] = Path(line).stem
                    
                    tracks.append(current_track)
                    current_track = {}
            
            self.current_playlist = tracks
            self.current_track_index = 0
            return True
            
        except Exception as e:
            print(f"Error loading playlist: {e}")
            return False
    
    def play(self, track_index=None):
        """Play a track from the current playlist"""
        if track_index is not None:
            self.current_track_index = track_index
        
        if not self.current_playlist:
            return False
        
        if self.current_track_index >= len(self.current_playlist):
            self.current_track_index = 0
        
        track = self.current_playlist[self.current_track_index]
        track_path = track['path']
        
        try:
            # Check if file exists
            if not os.path.exists(track_path):
                print(f"Track not found: {track_path}")
                return False
            
            if self.audio_available:
                pygame.mixer.music.load(track_path)
                pygame.mixer.music.play()
            else:
                print(f"Simulating playback of: {track_path}")
            
            self.is_playing = True
            self.is_paused = False
            self.is_crossfading = False
            self.next_track_queued = False
            
            # Start monitoring thread
            if self.monitor_thread is None or not self.monitor_thread.is_alive():
                self.stop_monitoring.clear()
                self.monitor_thread = Thread(target=self._monitor_playback)
                self.monitor_thread.daemon = True
                self.monitor_thread.start()
            
            return True
            
        except Exception as e:
            print(f"Error playing track: {e}")
            return False
    
    def pause(self):
        """Pause playback"""
        if self.is_playing and not self.is_paused:
            if self.audio_available:
                pygame.mixer.music.pause()
            self.is_paused = True
    
    def resume(self):
        """Resume playback"""
        if self.is_paused:
            if self.audio_available:
                pygame.mixer.music.unpause()
            self.is_paused = False
        elif not self.is_playing and self.current_playlist:
            self.play()
    
    def stop(self):
        """Stop playback"""
        if self.audio_available:
            pygame.mixer.music.stop()
        self.is_playing = False
        self.is_paused = False
    
    def next(self):
        """Skip to next track"""
        if self.current_playlist:
            self.current_track_index = (self.current_track_index + 1) % len(self.current_playlist)
            self.is_crossfading = False
            self.next_track_queued = False
            self.play()
    
    def previous(self):
        """Go to previous track"""
        if self.current_playlist:
            self.current_track_index = (self.current_track_index - 1) % len(self.current_playlist)
            self.is_crossfading = False
            self.next_track_queued = False
            self.play()
    
    def set_volume(self, volume):
        """Set volume (0-100)"""
        self.volume = volume / 100.0
        if self.audio_available:
            pygame.mixer.music.set_volume(self.volume)
    
    def get_status(self):
        """Get current playback status"""
        status = {
            'is_playing': self.is_playing and not self.is_paused,
            'is_paused': self.is_paused,
            'volume': int(self.volume * 100),
            'playlist_length': len(self.current_playlist),
            'current_track_index': self.current_track_index if self.current_playlist else None,
            'current_track': None
        }
        
        if self.current_playlist and self.current_track_index < len(self.current_playlist):
            track = self.current_playlist[self.current_track_index]
            status['current_track'] = {
                'title': track.get('title', 'Unknown'),
                'path': track.get('path', ''),
                'duration': track.get('duration', 'Unknown')
            }
        
        return status
    
    def _monitor_playback(self):
        """Monitor playback and handle crossfading to next track"""
        while not self.stop_monitoring.is_set():
            if self.is_playing and not self.is_paused:
                if self.audio_available:
                    if not pygame.mixer.music.get_busy():
                        # Track finished, play next
                        self.next()
                    elif self.crossfade_config.get('enabled', False):
                        # Check if we should start crossfading
                        self._handle_crossfade()
                # In no-audio mode, don't auto-advance
            elif not self.is_playing:
                # Stop monitoring if playback is stopped
                break
            
            time.sleep(0.1)  # Check more frequently for smooth crossfading
    
    def _handle_crossfade(self):
        """Handle crossfade logic during playback"""
        if not self.audio_available or self.is_crossfading:
            return
        
        try:
            # Get current position in milliseconds
            pos_ms = pygame.mixer.music.get_pos()
            
            # Get track duration (if available)
            if self.current_playlist and self.current_track_index < len(self.current_playlist):
                track = self.current_playlist[self.current_track_index]
                duration_str = track.get('duration', '0')
                
                try:
                    duration_sec = float(duration_str)
                    duration_ms = duration_sec * 1000
                    
                    # Calculate when to start crossfade
                    fade_start_before_end = self.crossfade_config.get('fade_out_start_before_end_ms', 5000)
                    crossfade_duration = self.crossfade_config.get('duration_ms', 3000)
                    
                    # Time remaining in track
                    time_remaining_ms = duration_ms - pos_ms
                    
                    # Start crossfade if we're close enough to the end
                    if time_remaining_ms <= fade_start_before_end and not self.next_track_queued:
                        self._start_crossfade(crossfade_duration)
                        
                except (ValueError, TypeError):
                    # If duration is unknown, let track finish naturally
                    pass
                    
        except Exception as e:
            print(f"Error in crossfade handling: {e}")
    
    def _start_crossfade(self, fade_duration_ms):
        """Start crossfading to the next track"""
        if not self.audio_available or not self.current_playlist:
            return
        
        try:
            # Calculate next track index
            next_track_index = (self.current_track_index + 1) % len(self.current_playlist)
            if next_track_index >= len(self.current_playlist):
                return
            
            next_track = self.current_playlist[next_track_index]
            next_track_path = next_track['path']
            
            # Check if next file exists
            if not os.path.exists(next_track_path):
                print(f"Next track not found: {next_track_path}")
                return
            
            # Queue the next track with fadeout
            self.is_crossfading = True
            self.next_track_queued = True
            
            # Fade out current track and automatically play next
            # pygame.mixer.music.fadeout() stops the current music after fading
            # We'll use queue() to preload the next track
            pygame.mixer.music.queue(next_track_path)
            pygame.mixer.music.set_endevent(pygame.USEREVENT)
            
            # Start fade out of current track
            pygame.mixer.music.fadeout(fade_duration_ms)
            
            # Update current track index when fade completes
            # The monitoring loop will detect when music stops and update
            print(f"Crossfading: {fade_duration_ms}ms fade to next track")
            
        except Exception as e:
            print(f"Error starting crossfade: {e}")
            self.is_crossfading = False
            self.next_track_queued = False
    
    def update_crossfade_config(self, config):
        """Update crossfade configuration"""
        if config:
            self.crossfade_config.update(config)
            print(f"Crossfade config updated: {self.crossfade_config}")
    
    def get_crossfade_config(self):
        """Get current crossfade configuration"""
        return self.crossfade_config.copy()
