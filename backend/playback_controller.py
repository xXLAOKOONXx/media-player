"""
Playback Controller
Handles audio playback using pygame with crossfading support
"""

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("Warning: pygame not available, running in simulation mode")

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    print("Warning: pydub not available, partial loading disabled")

import os
from pathlib import Path
from threading import Thread, Event
import time
import random
import copy
import logging
import re
import tempfile

from audio_metadata import MUTAGEN_AVAILABLE, display_title, read_audio_metadata

# Configure logging for performance monitoring
# Note: This is a module-level logger. Applications can configure the root logger
# to control this logger's behavior without being overridden.
logger = logging.getLogger('PlaybackController')
if not logger.handlers:  # Only configure if not already configured
    logger.setLevel(logging.INFO)  # Default level, can be changed by application


_WINDOWS_ABS_PATH_RE = re.compile(r'^[A-Za-z]:[\\/]')


def _is_url_path(value: str) -> bool:
    # Be conservative: M3U can contain http(s) streams.
    return '://' in value or value.startswith(('http:', 'https:'))


def _normalize_m3u_entry_path(value: str) -> str:
    """Normalize a single M3U path line for cross-platform compatibility.

    - Treat backslashes as path separators for file paths.
    - Leave URLs untouched.
    """
    if not value:
        return value
    if _is_url_path(value):
        return value
    return value.replace('\\', '/')


def _display_title(track: dict) -> str:
    # Backwards-compat wrapper for any internal calls.
    return display_title(track)


def _is_absolute_path_cross_platform(value: str) -> bool:
    """Return True for both POSIX-absolute paths and Windows-absolute paths.

    This prevents incorrect joining like `/playlist/dir/C:/Music/track.mp3` on Linux.
    """
    if not value:
        return False
    if os.path.isabs(value):
        return True
    # Windows drive letter paths (e.g. C:/Music/file.mp3)
    if _WINDOWS_ABS_PATH_RE.match(value):
        return True
    # UNC paths (e.g. //server/share/file.mp3)
    if value.startswith('//'):
        return True
    return False


class PlaybackController:
    """Controls audio playback with crossfading"""
    
    # Crossfade constants
    CROSSFADE_VOLUME_STEPS = 100  # Number of volume adjustment steps during crossfade
    CROSSFADE_LOG_FREQUENCY = 20  # Log every Nth step (100/20 = 5 log entries)
    FADEOUT_BUFFER_SECONDS = 0.5  # Buffer time to ensure fadeout and queue transition complete
    PRELOAD_BEFORE_CROSSFADE_MS = 15000  # Pre-load next track 15 seconds before crossfade starts
    
    def __init__(self, crossfade_config=None):
        # Initialize pygame mixer
        self.audio_available = False
        if PYGAME_AVAILABLE:
            try:
                # Initialize with more channels for crossfade support
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
                pygame.mixer.set_num_channels(8)  # Allow multiple simultaneous sounds
                self.audio_available = True
                logger.info("Pygame mixer initialized successfully")
            except Exception as e:
                logger.warning(f"Audio initialization failed: {e}")
                print("Running in no-audio mode. Playback will be simulated.")
        else:
            logger.warning("pygame not installed, running in no-audio mode")
        
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
        
        # Crossfade state for overlapping playback
        self.is_crossfading = False
        self.crossfade_start_time = None
        self.next_track_queued = False
        self.crossfade_thread = None
        
        # Pre-loaded next track for smoother crossfade (reduces CPU spike)
        self.preloaded_sound = None
        self.preloaded_track_index = None
        self.preload_thread = None
        self.preloaded_temp_file = None  # Track temp file for cleanup
        
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
    
    def _read_id3_metadata(self, file_path):
        """Read metadata from ID3 tags
        
        Returns dict with artist, album, duration, and timing information
        """
        # Shared implementation used by both Music + Player.
        # Include duration (for crossfade timing) + custom times.
        try:
            return read_audio_metadata(
                file_path,
                include_duration=True,
                include_times=True,
                include_tags=False,
            )
        except Exception as e:
            logger.error(f"Error reading audio metadata from {file_path}: {e}")
            return {}

    def _ensure_track_metadata(self, track: dict) -> None:
        """Best-effort: populate missing title/duration/artist/album from file metadata.

        This is intentionally one-time per track to avoid repeated disk/network I/O
        during frequent status polling.
        """
        if not isinstance(track, dict):
            return
        if track.get('_metadata_enriched') is True:
            return

        path = track.get('path')
        if not isinstance(path, str) or not path:
            track['_metadata_enriched'] = True
            return

        # Only attempt if metadata might help.
        duration_val = track.get('duration')
        has_duration = False
        if isinstance(duration_val, (int, float)):
            has_duration = True
        elif isinstance(duration_val, str):
            try:
                float(duration_val)
                has_duration = True
            except ValueError:
                has_duration = False

        title_val = track.get('title')
        needs_title = not (isinstance(title_val, str) and title_val.strip())
        needs_metadata = needs_title or (not has_duration) or (track.get('artist') is None) or (track.get('album') is None)

        if not needs_metadata:
            track['_metadata_enriched'] = True
            return

        if not os.path.exists(path):
            track['_metadata_enriched'] = True
            return

        if not MUTAGEN_AVAILABLE:
            track['title'] = display_title(track)
            track['_metadata_enriched'] = True
            return

        try:
            metadata = read_audio_metadata(
                path,
                include_duration=True,
                include_times=True,
                include_tags=False,
            )
            if isinstance(metadata, dict) and metadata:
                track.update(metadata)
        except Exception:
            pass

        track['title'] = display_title(track)
        track['_metadata_enriched'] = True
    
    def _read_id3_times(self, file_path):
        """Read start and end times from ID3 tags
        
        Returns tuple (start_time_seconds, end_time_seconds) or (None, None)
        Times in ID3 are stored in milliseconds, converted to seconds here
        """
        metadata = self._read_id3_metadata(file_path)
        return metadata.get('start_time'), metadata.get('end_time')
    
    def load_playlist(self, playlist_path):
        """Load a playlist from M3U file"""
        try:
            tracks = []
            playlist_dir = Path(playlist_path).parent
            
            # Use utf-8-sig encoding to automatically strip BOM if present
            with open(playlist_path, 'r', encoding='utf-8-sig') as f:
                lines = f.readlines()
            
            current_track = {}
            for line in lines:
                # Strip whitespace (BOM is already handled by encoding)
                line = line.strip()
                
                # Skip empty lines
                if not line:
                    continue
                
                # Process comment/directive lines starting with #
                if line.startswith('#'):
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
                    
                    # Skip all other comment/directive lines (including #EXTM3U and unknown directives)
                    continue
                
                # This is a file path (non-comment line)
                line = _normalize_m3u_entry_path(line)
                # Handle relative paths
                if not _is_absolute_path_cross_platform(line) and not _is_url_path(line):
                    line = str(playlist_dir / line)
                
                current_track['path'] = line
                if 'title' not in current_track:
                    current_track['title'] = Path(line).stem
                
                # Read ID3 tags for metadata (takes precedence over M3U directives)
                if os.path.exists(line):
                    metadata = self._read_id3_metadata(line)
                    # Title (takes precedence over filename / EXTINF)
                    if 'title' in metadata and isinstance(metadata['title'], str) and metadata['title'].strip():
                        current_track['title'] = metadata['title']
                    # Duration from audio file (takes precedence over M3U duration)
                    if 'duration' in metadata:
                        current_track['duration'] = str(metadata['duration'])
                        logger.debug(f"Using actual duration from audio file: {metadata['duration']}s")
                    # Artist and album
                    if 'artist' in metadata:
                        current_track['artist'] = metadata['artist']
                    if 'album' in metadata:
                        current_track['album'] = metadata['album']
                    # Start/end times (takes precedence)
                    if 'start_time' in metadata:
                        current_track['start_time'] = metadata['start_time']
                    if 'end_time' in metadata:
                        current_track['end_time'] = metadata['end_time']
                
                tracks.append(current_track)
                current_track = {}
            
            self.current_playlist = tracks
            self.original_playlist = copy.deepcopy(tracks)  # Deep copy for full isolation
            self.current_track_index = 0
            
            # Apply shuffle if enabled - for new playlists, don't preserve current track
            if self.shuffle_enabled:
                self._apply_shuffle(preserve_current=False)
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading playlist: {e}")
            return False
    
    def _reset_crossfade_state(self):
        """Reset crossfade state"""
        self.is_crossfading = False
        self.next_track_queued = False
    
    def _reset_preload_state(self):
        """Reset pre-load state and clear thread reference"""
        self.preloaded_sound = None
        self.preloaded_track_index = None
        self.preload_thread = None  # Clear reference for garbage collection
        
        # Clean up temporary file if exists
        if self.preloaded_temp_file and os.path.exists(self.preloaded_temp_file):
            try:
                os.remove(self.preloaded_temp_file)
                logger.debug(f"Cleaned up temporary file: {self.preloaded_temp_file}")
            except Exception as e:
                logger.warning(f"Failed to clean up temp file: {e}")
        self.preloaded_temp_file = None
    
    def _preload_next_track(self, next_track_index, next_track_path):
        """Pre-load only the first few seconds of next track to reduce CPU spike
        
        Uses pydub to extract just the crossfade duration + 1 second buffer.
        This significantly reduces memory usage and loading time.
        
        Args:
            next_track_index: Index of the track to pre-load
            next_track_path: Path to the audio file to pre-load
        """
        if not self.audio_available:
            return
        
        # Check if a preload thread is already running
        if self.preload_thread is not None and self.preload_thread.is_alive():
            logger.debug("Pre-load already in progress, skipping")
            return
        
        def load_in_background():
            try:
                # Calculate how many seconds we need to extract
                fade_duration_ms = self.crossfade_config.get('duration_ms', 3000)
                # Extract crossfade duration + 1 second buffer
                extract_duration_ms = fade_duration_ms + 1000
                
                logger.info(f"Partial loading first {extract_duration_ms}ms of: {Path(next_track_path).name}")
                
                # Try partial loading with pydub
                if PYDUB_AVAILABLE:
                    try:
                        # Load only the first N milliseconds of the audio file
                        audio = AudioSegment.from_file(next_track_path)
                        partial_audio = audio[:extract_duration_ms]
                        
                        # Export to temporary WAV file
                        temp_fd, temp_path = tempfile.mkstemp(suffix='.wav', prefix='crossfade_')
                        os.close(temp_fd)  # Close file descriptor, we'll use the path
                        
                        partial_audio.export(temp_path, format='wav')
                        logger.info(f"Exported {len(partial_audio)}ms snippet to temp file")
                        
                        # Load the partial audio as a pygame Sound
                        next_sound = pygame.mixer.Sound(temp_path)
                        
                        # Only store if we haven't moved to another track
                        if self.is_playing and self.preloaded_track_index == next_track_index:
                            self.preloaded_sound = next_sound
                            self.preloaded_temp_file = temp_path
                            logger.info(f"Successfully pre-loaded partial track ({next_sound.get_length():.2f}s snippet)")
                        else:
                            logger.debug("Track changed during pre-load, discarding")
                            # Clean up temp file if not used
                            try:
                                os.remove(temp_path)
                            except:
                                pass
                        
                    except Exception as e:
                        logger.warning(f"Partial loading with pydub failed: {e}")
                        # Fall back to loading full file
                        next_sound = pygame.mixer.Sound(next_track_path)
                        if self.is_playing and self.preloaded_track_index == next_track_index:
                            self.preloaded_sound = next_sound
                            logger.info(f"Fell back to full file loading (size: {next_sound.get_length():.2f}s)")
                else:
                    # pydub not available, load full file
                    logger.info("pydub not available, loading full file")
                    next_sound = pygame.mixer.Sound(next_track_path)
                    if self.is_playing and self.preloaded_track_index == next_track_index:
                        self.preloaded_sound = next_sound
                        logger.info(f"Pre-loaded full track (size: {next_sound.get_length():.2f}s)")
                    
            except pygame.error as e:
                logger.info(f"Cannot pre-load track as Sound: {e}")
                # This is not critical - crossfade will fall back to queue method
            except Exception as e:
                logger.warning(f"Error pre-loading track: {e}")
        
        # Start background loading thread
        self.preload_thread = Thread(target=load_in_background)
        self.preload_thread.daemon = True
        self.preload_thread.start()

    
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
                logger.warning(f"Track not found: {track_path}")
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
                logger.info(f"Simulating playback of: {track_path}")
                if self.track_custom_start is not None:
                    logger.info(f"  Starting at: {self.track_custom_start}s")
                if self.track_custom_end is not None:
                    logger.info(f"  Ending at: {self.track_custom_end}s")
            
            self.is_playing = True
            self.is_paused = False
            self.track_start_time = time.time()
            self.pause_time = None
            self.total_pause_duration = 0
            self._reset_crossfade_state()
            self._reset_preload_state()
            
            # Start monitoring thread
            if self.monitor_thread is None or not self.monitor_thread.is_alive():
                self.stop_monitoring.clear()
                self.monitor_thread = Thread(target=self._monitor_playback)
                self.monitor_thread.daemon = True
                self.monitor_thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"Error playing track: {e}")
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
        self._reset_preload_state()
    
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
            'next_track': None,
            'shuffle': self.shuffle_enabled,
            'repeat_mode': self.repeat_mode,
            'current_position': self.get_current_position()
        }
        
        if self.current_playlist and self.current_track_index < len(self.current_playlist):
            track = self.current_playlist[self.current_track_index]
            self._ensure_track_metadata(track)
            status['current_track'] = {
                'title': _display_title(track),
                'path': track.get('path', ''),
                'duration': track.get('duration', 'Unknown'),
                'start_time': track.get('start_time'),
                'end_time': track.get('end_time'),
                'artist': track.get('artist'),
                'album': track.get('album')
            }
            
            # Get next track information
            next_track_index = self.current_track_index + 1
            if next_track_index < len(self.current_playlist):
                next_track = self.current_playlist[next_track_index]
                status['next_track'] = {
                    'title': _display_title(next_track),
                    'artist': next_track.get('artist'),
                    'album': next_track.get('album')
                }
            elif self.repeat_mode == 'all' and len(self.current_playlist) > 0:
                # If repeat all is on, next track is the first track
                next_track = self.current_playlist[0]
                status['next_track'] = {
                    'title': _display_title(next_track),
                    'artist': next_track.get('artist'),
                    'album': next_track.get('album')
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
                            logger.info(f"Reached custom end time: {self.track_custom_end}s")
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
            # Calculate elapsed time since track start
            if self.track_start_time is None:
                return
            
            elapsed = time.time() - self.track_start_time - self.total_pause_duration
            current_position = (self.track_custom_start or 0) + elapsed
            
            # Get track duration (if available)
            if self.current_playlist and self.current_track_index < len(self.current_playlist):
                track = self.current_playlist[self.current_track_index]
                duration_str = track.get('duration', '0')
                
                # Determine effective end time
                if self.track_custom_end is not None:
                    effective_end_time = self.track_custom_end
                else:
                    try:
                        effective_end_time = float(duration_str)
                    except (ValueError, TypeError):
                        return  # Can't determine duration
                
                # Calculate when to start crossfade
                fade_start_before_end_ms = self.crossfade_config.get('fade_out_start_before_end_ms', 5000)
                fade_start_time = effective_end_time - (fade_start_before_end_ms / 1000.0)
                
                # Calculate when to pre-load next track (earlier than crossfade)
                preload_start_time = effective_end_time - ((fade_start_before_end_ms + self.PRELOAD_BEFORE_CROSSFADE_MS) / 1000.0)
                
                # Pre-load next track early to spread CPU load
                # Check both index and thread status to prevent duplicate preloads
                if (current_position >= preload_start_time and 
                    self.preloaded_track_index is None and
                    (self.preload_thread is None or not self.preload_thread.is_alive())):
                    # Determine next track to pre-load
                    if self.repeat_mode == 'one':
                        # Don't pre-load in repeat one mode
                        pass
                    else:
                        next_track_index = self.current_track_index + 1
                        
                        if next_track_index >= len(self.current_playlist):
                            if self.repeat_mode == 'all':
                                next_track_index = 0
                            else:
                                # No next track to pre-load
                                return
                        
                        next_track = self.current_playlist[next_track_index]
                        next_track_path = next_track['path']
                        
                        # Check if next file exists
                        if os.path.exists(next_track_path):
                            # Set index first to prevent race condition
                            self.preloaded_track_index = next_track_index
                            self._preload_next_track(next_track_index, next_track_path)
                
                # Start crossfade if we've reached the fade start time
                if current_position >= fade_start_time and not self.next_track_queued:
                    crossfade_duration_ms = self.crossfade_config.get('duration_ms', 3000)
                    logger.info(f"Starting crossfade at {current_position:.2f}s (track ends at {effective_end_time:.2f}s)")
                    self._start_crossfade(crossfade_duration_ms)
                    
        except Exception as e:
            logger.error(f"Error in crossfade handling: {e}")
    
    def _start_crossfade(self, fade_duration_ms):
        """Start crossfading to the next track with real overlap using Sound channels
        
        Note: This approach loads audio into memory for the crossfade period.
        For very large files, this may cause memory issues, but it's the only way
        to achieve true simultaneous playback overlap with pygame.
        """
        if not self.audio_available or not self.current_playlist:
            return
        
        try:
            # Determine next track index based on repeat mode
            if self.repeat_mode == 'one':
                # Don't crossfade in repeat one mode, just let it replay
                return
            
            next_track_index = self.current_track_index + 1
            
            if next_track_index >= len(self.current_playlist):
                if self.repeat_mode == 'all':
                    next_track_index = 0
                else:
                    # No next track and no repeat, let current track finish
                    return
            
            next_track = self.current_playlist[next_track_index]
            next_track_path = next_track['path']
            
            # Check if next file exists
            if not os.path.exists(next_track_path):
                logger.warning(f"Next track not found: {next_track_path}")
                return
            
            self.is_crossfading = True
            self.next_track_queued = True
            self.crossfade_start_time = time.time()
            
            fade_duration_seconds = fade_duration_ms / 1000.0
            
            logger.info(f"Starting crossfade: {fade_duration_ms}ms overlap between tracks")
            
            # Helper function to update state after fallback fade completes
            def create_fallback_update(delay_seconds):
                """Creates a function to update state after fallback fadeout completes
                
                Args:
                    delay_seconds: Time to wait before updating state (fade duration + buffer)
                """
                def update_state_after_fade():
                    time.sleep(delay_seconds)
                    if self.is_playing:
                        self.current_track_index = next_track_index
                        self.track_start_time = time.time()
                        self.pause_time = None
                        self.total_pause_duration = 0
                        
                        next_track_obj = self.current_playlist[self.current_track_index]
                        self.track_custom_start = next_track_obj.get('start_time')
                        self.track_custom_end = next_track_obj.get('end_time')
                        
                        pygame.mixer.music.set_volume(self.volume)
                    self._reset_crossfade_state()
                    self._reset_preload_state()
                return update_state_after_fade
            
            # Start a thread to handle the crossfade
            def execute_crossfade():
                try:
                    # Get current volume for fade calculations
                    current_volume = pygame.mixer.music.get_volume()
                    
                    # Capture pre-loaded sound reference atomically to avoid race condition
                    preloaded_sound_ref = self.preloaded_sound
                    preloaded_index_ref = self.preloaded_track_index
                    
                    # Try to use pre-loaded sound if available
                    next_sound = None
                    if preloaded_sound_ref is not None and preloaded_index_ref == next_track_index:
                        logger.info("Using pre-loaded next track (reduces CPU spike)")
                        next_sound = preloaded_sound_ref
                    
                    # Load next track as Sound object for simultaneous playback
                    if next_sound is None:
                        try:
                            logger.info(f"Loading next track into memory for overlap playback")
                            next_sound = pygame.mixer.Sound(next_track_path)
                            logger.info(f"Successfully loaded next track as Sound object (size: {next_sound.get_length():.2f}s)")
                        except pygame.error as e:
                            logger.warning(f"Cannot load track as Sound (possibly too large): {e}")
                            next_sound = None
                    
                    # Check if we have a sound to work with
                    if next_sound is not None:
                        next_channel = pygame.mixer.find_channel()
                        
                        if next_channel is None:
                            logger.warning("No available channel for crossfade, using queue method instead")
                            # Fallback to queue method - let the monitoring thread handle the transition
                            pygame.mixer.music.queue(next_track_path)
                            pygame.mixer.music.fadeout(fade_duration_ms)
                            
                            # Schedule state update when fadeout completes
                            update_func = create_fallback_update(fade_duration_seconds)
                            Thread(target=update_func, daemon=True).start()
                            return
                    else:
                        # Could not load as Sound object, use fallback queue method
                        logger.info("Falling back to simple queue-based crossfade")
                        pygame.mixer.music.queue(next_track_path)
                        pygame.mixer.music.fadeout(fade_duration_ms)
                        
                        # Schedule state update after fade completes
                        update_func = create_fallback_update(fade_duration_seconds + self.FADEOUT_BUFFER_SECONDS)
                        Thread(target=update_func, daemon=True).start()
                        return
                    
                    # Now we have both: current track playing via mixer.music and next track loaded as Sound
                    # Perform simultaneous fade out/in
                    start_time = time.time()
                    steps = self.CROSSFADE_VOLUME_STEPS
                    step_duration = fade_duration_seconds / steps
                    
                    # Start playing next track at volume 0
                    next_sound.set_volume(0.0)
                    next_channel.play(next_sound)
                    next_start_time = time.time()
                    
                    logger.info("Both tracks now playing - performing simultaneous fade")
                    
                    # Gradually fade out current track and fade in next track
                    for i in range(steps):
                        if not self.is_crossfading:
                            next_channel.stop()
                            break
                        
                        elapsed = time.time() - start_time
                        progress = min(elapsed / fade_duration_seconds, 1.0)
                        
                        # Fade out current track (music)
                        current_vol = current_volume * (1.0 - progress)
                        pygame.mixer.music.set_volume(current_vol)
                        
                        # Fade in next track (sound channel)
                        next_vol = self.volume * progress
                        next_sound.set_volume(next_vol)
                        
                        # Log periodically to avoid too many log entries
                        if i % self.CROSSFADE_LOG_FREQUENCY == 0:
                            logger.debug(f"Crossfade {progress*100:.0f}%: current={current_vol:.2f}, next={next_vol:.2f}")
                        
                        time.sleep(step_duration)
                    
                    # Crossfade complete - stop old track and switch to music player for new track
                    pygame.mixer.music.stop()
                    next_channel.stop()
                    
                    # Now play the next track normally via mixer.music
                    self.current_track_index = next_track_index
                    next_track_obj = self.current_playlist[self.current_track_index]
                    self.track_custom_start = next_track_obj.get('start_time')
                    self.track_custom_end = next_track_obj.get('end_time')
                    
                    # Calculate how much of the next track we already played
                    played_duration = time.time() - next_start_time
                    
                    # Load and play from current position
                    pygame.mixer.music.load(next_track_path)
                    start_pos = (self.track_custom_start or 0) + played_duration
                    pygame.mixer.music.play(start=start_pos)
                    pygame.mixer.music.set_volume(self.volume)
                    
                    # Update timing
                    self.track_start_time = time.time() - played_duration
                    self.pause_time = None
                    self.total_pause_duration = 0
                    
                    logger.info(f"Crossfade complete - now playing: {next_track_obj.get('title', 'Unknown')}")
                    
                    self._reset_crossfade_state()
                    self._reset_preload_state()
                    
                except Exception as e:
                    logger.error(f"Error in crossfade execution: {e}", exc_info=True)
                    self._reset_crossfade_state()
                    self._reset_preload_state()
                    # Restore volume in case of error
                    if self.audio_available:
                        pygame.mixer.music.set_volume(self.volume)
            
            self.crossfade_thread = Thread(target=execute_crossfade)
            self.crossfade_thread.daemon = True
            self.crossfade_thread.start()
            
        except Exception as e:
            logger.error(f"Error starting crossfade: {e}")
            self._reset_crossfade_state()
    
    def update_crossfade_config(self, config):
        """Update crossfade configuration"""
        if config:
            self.crossfade_config.update(config)
            logger.info(f"Crossfade config updated: {self.crossfade_config}")
    
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
                'title': _display_title(track),
                'path': track.get('path', ''),
                'duration': track.get('duration', 'Unknown'),
                'start_time': track.get('start_time'),
                'end_time': track.get('end_time'),
                'artist': track.get('artist'),
                'album': track.get('album')
            }
            for i, track in enumerate(self.current_playlist)
        ]
    
    def set_shuffle(self, enabled):
        """Enable or disable shuffle mode"""
        self.shuffle_enabled = enabled
        
        if enabled:
            self._apply_shuffle(preserve_current=True)
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
    
    def _apply_shuffle(self, preserve_current=True):
        """Apply shuffle to current playlist
        
        Args:
            preserve_current: If True, keeps the current track at position 0.
                            If False, shuffles all tracks randomly (for new playlists).
        """
        if not self.current_playlist:
            return
        
        # Save current track if needed
        current_track = None
        if preserve_current and self.current_track_index < len(self.current_playlist):
            current_track = self.current_playlist[self.current_track_index]
        
        # Shuffle the playlist
        shuffled = self.current_playlist.copy()
        random.shuffle(shuffled)
        
        # If there's a current track and we want to preserve it, move it to position 0
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
                logger.info(f"Simulating seek to {position}s")
                return True
                
        except Exception as e:
            logger.error(f"Error seeking: {e}")
            return False
    
    def play_sound_effect(self, sound_path):
        """Play a sound effect in parallel with music using a separate channel"""
        if not os.path.exists(sound_path):
            logger.error(f"Sound effect file not found: {sound_path}")
            return False
        
        try:
            if self.audio_available:
                # Load and play sound effect on a separate channel
                sound = pygame.mixer.Sound(sound_path)
                channel = pygame.mixer.find_channel()
                
                if channel:
                    channel.play(sound)
                    logger.info(f"Playing sound effect: {sound_path}")
                    return True
                else:
                    logger.warning("No available channel for sound effect")
                    return False
            else:
                logger.info(f"Simulating sound effect: {sound_path}")
                return True
                
        except Exception as e:
            logger.error(f"Error playing sound effect: {e}")
            return False
