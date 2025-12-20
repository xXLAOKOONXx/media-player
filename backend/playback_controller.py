"""
Playback Controller
Handles audio playback using pygame with crossfading support
"""

import pygame
import os
from pathlib import Path
from threading import Thread, Event
import time
from mutagen import File as MutagenFile


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
        self.original_playlist = []  # Store original order for shuffle
        self.current_track_index = 0
        self.is_playing = False
        self.is_paused = False
        self.volume = 0.5
        
        # Shuffle and repeat modes
        self.shuffle_enabled = False
        self.repeat_mode = 'none'  # 'none', 'all', 'one'
        
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
        
        # Track timing state
        self.track_start_time = None  # System time when track started
        self.track_custom_start = None  # Custom start time in track (seconds)
        self.track_custom_end = None  # Custom end time in track (seconds)
        self.pause_time = None  # System time when paused
        self.total_pause_duration = 0  # Total time spent paused
        
        # Set initial volume if audio is available
        if self.audio_available:
            pygame.mixer.music.set_volume(self.volume)
        
        # Playback monitoring thread
        self.monitor_thread = None
        self.stop_monitoring = Event()
    
    def _read_id3_times(self, file_path):
        """Read start and end times from ID3 tags
        
        Returns tuple (start_time_seconds, end_time_seconds) or (None, None)
        Times in ID3 are stored in milliseconds, converted to seconds here
        """
        try:
            audio = MutagenFile(file_path)
            if audio is None:
                return None, None
            
            start_time = None
            end_time = None
            
            # Check for custom ID3 fields: LAO:MUSIC_START and LAO:MUSIC_END
            # These are stored in TXXX frames in ID3v2
            if hasattr(audio, 'tags') and audio.tags:
                # Try to get TXXX frames (user-defined text information)
                txxx_frames = audio.tags.getall('TXXX')
                for frame in txxx_frames:
                    desc = str(frame.desc) if hasattr(frame, 'desc') else ''
                    if desc == 'LAO:MUSIC_START':
                        try:
                            # Value is in milliseconds, convert to seconds
                            start_time = float(frame.text[0]) / 1000.0
                        except (ValueError, IndexError, TypeError):
                            pass
                    elif desc == 'LAO:MUSIC_END':
                        try:
                            # Value is in milliseconds, convert to seconds
                            end_time = float(frame.text[0]) / 1000.0
                        except (ValueError, IndexError, TypeError):
                            pass
            
            return start_time, end_time
            
        except Exception as e:
            print(f"Error reading ID3 tags from {file_path}: {e}")
            return None, None
    
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
                
                elif line.startswith('#EXTVLCOPT:'):
                    # Parse VLC-style options for start/stop times (fallback if ID3 tags not present)
                    # Format: #EXTVLCOPT:start-time=10.5
                    # Format: #EXTVLCOPT:stop-time=120.5
                    option = line[11:].strip()
                    if option.startswith('start-time='):
                        try:
                            # Only set if not already set from previous source
                            if 'start_time' not in current_track:
                                current_track['start_time'] = float(option.split('=')[1])
                        except (ValueError, IndexError):
                            pass
                    elif option.startswith('stop-time='):
                        try:
                            # Only set if not already set from previous source
                            if 'end_time' not in current_track:
                                current_track['end_time'] = float(option.split('=')[1])
                        except (ValueError, IndexError):
                            pass
                
                elif line and not line.startswith('#'):
                    # This is a file path
                    # Handle relative paths
                    if not os.path.isabs(line):
                        line = str(playlist_dir / line)
                    
                    current_track['path'] = line
                    if 'title' not in current_track:
                        current_track['title'] = Path(line).stem
                    
                    # Read ID3 tags for start/end times (takes precedence over M3U directives)
                    if os.path.exists(line):
                        id3_start, id3_end = self._read_id3_times(line)
                        if id3_start is not None:
                            current_track['start_time'] = id3_start
                        if id3_end is not None:
                            current_track['end_time'] = id3_end
                    
                    tracks.append(current_track)
                    current_track = {}
            
            self.current_playlist = tracks
            self.original_playlist = tracks.copy()  # Store original order
            self.current_track_index = 0
            
            # Apply shuffle if enabled
            if self.shuffle_enabled:
                self._apply_shuffle()
            
            return True
            
        except Exception as e:
            print(f"Error loading playlist: {e}")
            return False
    
    def _reset_crossfade_state(self):
        """Reset crossfade state"""
        self.is_crossfading = False
        self.next_track_queued = False
    
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
            
            # Get custom start and end times if specified
            self.track_custom_start = track.get('start_time')
            self.track_custom_end = track.get('end_time')
            
            if self.audio_available:
                pygame.mixer.music.load(track_path)
                
                # If custom start time is specified, seek to that position
                if self.track_custom_start is not None:
                    pygame.mixer.music.play(start=self.track_custom_start)
                else:
                    pygame.mixer.music.play()
            else:
                print(f"Simulating playback of: {track_path}")
                if self.track_custom_start is not None:
                    print(f"  Starting at: {self.track_custom_start}s")
                if self.track_custom_end is not None:
                    print(f"  Ending at: {self.track_custom_end}s")
            
            self.is_playing = True
            self.is_paused = False
            self.track_start_time = time.time()
            self.pause_time = None
            self.total_pause_duration = 0
            self._reset_crossfade_state()
            
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
            self.pause_time = time.time()
    
    def resume(self):
        """Resume playback"""
        if self.is_paused:
            if self.audio_available:
                pygame.mixer.music.unpause()
            self.is_paused = False
            # Track how long we were paused
            if self.pause_time is not None:
                self.total_pause_duration += time.time() - self.pause_time
                self.pause_time = None
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
            if self.repeat_mode == 'one':
                # Repeat current track
                self._reset_crossfade_state()
                self.play()
            else:
                # Move to next track
                self.current_track_index = self.current_track_index + 1
                
                if self.current_track_index >= len(self.current_playlist):
                    if self.repeat_mode == 'all':
                        # Loop back to start
                        self.current_track_index = 0
                    else:
                        # Stop at end (repeat mode 'none')
                        self.current_track_index = 0
                        self.stop()
                        return
                
                self._reset_crossfade_state()
                self.play()
    
    def previous(self):
        """Go to previous track"""
        if self.current_playlist:
            self.current_track_index = (self.current_track_index - 1) % len(self.current_playlist)
            self._reset_crossfade_state()
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
            'current_track': None,
            'shuffle': self.shuffle_enabled,
            'repeat_mode': self.repeat_mode,
            'current_position': self.get_current_position()
        }
        
        if self.current_playlist and self.current_track_index < len(self.current_playlist):
            track = self.current_playlist[self.current_track_index]
            status['current_track'] = {
                'title': track.get('title', 'Unknown'),
                'path': track.get('path', ''),
                'duration': track.get('duration', 'Unknown'),
                'start_time': track.get('start_time'),
                'end_time': track.get('end_time')
            }
        
        return status
    
    def _monitor_playback(self):
        """Monitor playback and handle crossfading to next track"""
        while not self.stop_monitoring.is_set():
            if self.is_playing and not self.is_paused:
                if self.audio_available:
                    # Check if custom end time has been reached
                    if self.track_custom_end is not None and self.track_start_time is not None:
                        elapsed = time.time() - self.track_start_time - self.total_pause_duration
                        effective_position = (self.track_custom_start or 0) + elapsed
                        
                        # If we've reached the custom end time, stop and move to next
                        if effective_position >= self.track_custom_end:
                            print(f"Reached custom end time: {self.track_custom_end}s")
                            self.next()
                            continue
                    
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
            # Note: pygame.mixer.music.get_pos() returns milliseconds since music started
            # This works for continuous playback but may be inaccurate after pause/resume
            # For more accurate tracking, would need to track pause duration separately
            pos_ms = pygame.mixer.music.get_pos()
            
            # Skip if track just started (position might be incorrect)
            if pos_ms < 1000:
                return
            
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
                    
                    # Time remaining in track (estimate)
                    time_remaining_ms = duration_ms - pos_ms
                    
                    # Start crossfade if we're close enough to the end
                    # Only if duration is available and seems reasonable
                    if duration_ms > fade_start_before_end and time_remaining_ms <= fade_start_before_end and not self.next_track_queued:
                        self._start_crossfade(crossfade_duration)
                        
                except (ValueError, TypeError):
                    # If duration is unknown or invalid, let track finish naturally
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
            
            # Queue next track to play after current one fades
            pygame.mixer.music.queue(next_track_path)
            
            # Start fade out of current track
            pygame.mixer.music.fadeout(fade_duration_ms)
            
            # Update current track index when fade completes
            # The monitoring loop will detect when music stops and update
            print(f"Crossfading: {fade_duration_ms}ms fade to next track")
            
        except Exception as e:
            print(f"Error starting crossfade: {e}")
            self._reset_crossfade_state()
    
    def update_crossfade_config(self, config):
        """Update crossfade configuration"""
        if config:
            self.crossfade_config.update(config)
            print(f"Crossfade config updated: {self.crossfade_config}")
    
    def get_crossfade_config(self):
        """Get current crossfade configuration"""
        return self.crossfade_config.copy()
    
    def set_track_times(self, track_index, start_time=None, end_time=None):
        """Set custom start and end times for a specific track in the playlist"""
        if not self.current_playlist or track_index < 0 or track_index >= len(self.current_playlist):
            return False
        
        # Validate input
        if start_time is not None and start_time < 0:
            return False
        
        if end_time is not None and end_time < 0:
            return False
        
        if start_time is not None and end_time is not None and start_time >= end_time:
            return False
        
        track = self.current_playlist[track_index]
        
        if start_time is not None:
            track['start_time'] = start_time
        else:
            track.pop('start_time', None)
        
        if end_time is not None:
            track['end_time'] = end_time
        else:
            track.pop('end_time', None)
        
        # If currently playing this track, update the runtime values
        if track_index == self.current_track_index and self.is_playing:
            self.track_custom_start = track.get('start_time')
            self.track_custom_end = track.get('end_time')
        
        return True
    
    def get_playlist_tracks(self):
        """Get all tracks in the current playlist with their custom times"""
        return [
            {
                'index': i,
                'title': track.get('title', 'Unknown'),
                'path': track.get('path', ''),
                'duration': track.get('duration', 'Unknown'),
                'start_time': track.get('start_time'),
                'end_time': track.get('end_time')
            }
            for i, track in enumerate(self.current_playlist)
        ]
    
    def set_shuffle(self, enabled):
        """Enable or disable shuffle mode"""
        self.shuffle_enabled = enabled
        
        if enabled:
            self._apply_shuffle()
        else:
            # Restore original order
            if self.original_playlist:
                # Find current track in original playlist
                current_track = None
                if self.current_playlist and self.current_track_index < len(self.current_playlist):
                    current_track = self.current_playlist[self.current_track_index]
                
                self.current_playlist = self.original_playlist.copy()
                
                # Update current track index to match in original order
                if current_track:
                    for i, track in enumerate(self.current_playlist):
                        if track.get('path') == current_track.get('path'):
                            self.current_track_index = i
                            break
        
        return True
    
    def _apply_shuffle(self):
        """Apply shuffle to current playlist"""
        if not self.current_playlist:
            return
        
        import random
        
        # Save current track
        current_track = None
        if self.current_track_index < len(self.current_playlist):
            current_track = self.current_playlist[self.current_track_index]
        
        # Shuffle the playlist
        shuffled = self.current_playlist.copy()
        random.shuffle(shuffled)
        
        # If there's a current track, move it to position 0
        if current_track:
            # Remove current track from shuffled list
            shuffled = [t for t in shuffled if t.get('path') != current_track.get('path')]
            # Insert at beginning
            shuffled.insert(0, current_track)
            self.current_track_index = 0
        
        self.current_playlist = shuffled
    
    def set_repeat_mode(self, mode):
        """Set repeat mode: 'none', 'all', or 'one'"""
        if mode not in ['none', 'all', 'one']:
            return False
        
        self.repeat_mode = mode
        return True
    
    def get_shuffle(self):
        """Get current shuffle state"""
        return self.shuffle_enabled
    
    def get_repeat_mode(self):
        """Get current repeat mode"""
        return self.repeat_mode
    
    def get_current_position(self):
        """Get current playback position in seconds"""
        if not self.is_playing or not self.track_start_time:
            return None
        
        # Calculate elapsed time
        if self.is_paused and self.pause_time:
            elapsed = self.pause_time - self.track_start_time - self.total_pause_duration
        else:
            elapsed = time.time() - self.track_start_time - self.total_pause_duration
        
        # Add custom start time if present
        position = (self.track_custom_start or 0) + elapsed
        
        return position
    
    def seek(self, position):
        """Seek to a specific position in the current track (in seconds)"""
        if not self.is_playing or not self.current_playlist:
            return False
        
        if self.current_track_index >= len(self.current_playlist):
            return False
        
        # Get current track
        track = self.current_playlist[self.current_track_index]
        track_path = track['path']
        
        # Check if file exists
        if not os.path.exists(track_path):
            return False
        
        try:
            if self.audio_available:
                # Stop current playback
                pygame.mixer.music.stop()
                
                # Reload and play from new position
                pygame.mixer.music.load(track_path)
                pygame.mixer.music.play(start=position)
                
                # Update state
                self.track_start_time = time.time()
                self.track_custom_start = position
                self.total_pause_duration = 0
                self.is_paused = False
                
                return True
            else:
                print(f"Simulating seek to {position}s")
                return True
                
        except Exception as e:
            print(f"Error seeking: {e}")
            return False
