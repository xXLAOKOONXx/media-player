"""
Playback Controller
Handles audio playback using pygame
"""

import pygame
import os
from pathlib import Path
from threading import Thread, Event
import time


class PlaybackController:
    """Controls audio playback"""
    
    def __init__(self):
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
            self.play()
    
    def previous(self):
        """Go to previous track"""
        if self.current_playlist:
            self.current_track_index = (self.current_track_index - 1) % len(self.current_playlist)
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
        """Monitor playback and auto-advance to next track"""
        while not self.stop_monitoring.is_set():
            if self.is_playing and not self.is_paused:
                if self.audio_available:
                    if not pygame.mixer.music.get_busy():
                        # Track finished, play next
                        self.next()
                # In no-audio mode, don't auto-advance
            elif not self.is_playing:
                # Stop monitoring if playback is stopped
                break
            
            time.sleep(0.5)
