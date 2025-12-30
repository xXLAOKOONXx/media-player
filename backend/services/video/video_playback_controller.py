"""
Video Playback Controller
Handles video playback using mpv player for server-side rendering
Falls back to state-only mode if mpv is not available
"""

try:
    import mpv
    MPV_AVAILABLE = True
except (ImportError, OSError):
    MPV_AVAILABLE = False
    print("Warning: python-mpv not available, video will only play client-side")

try:
    from mutagen.mp4 import MP4, MP4StreamInfoError
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False
    MP4 = None
    MP4StreamInfoError = None
    print("Warning: mutagen not available for video duration extraction")

import os
import hashlib
from pathlib import Path
import random
import copy
import logging
import time
import sys

from services.general.basic_file_operation import get_actual_path_with_correct_case
from services.video.video_metadata import read_video_metadata

# Configure logging
logger = logging.getLogger('VideoPlaybackController')
if not logger.handlers:
    logger.setLevel(logging.INFO)


def _running_under_pytest() -> bool:
    # Avoid initializing MPV during unit tests. python-mpv can spawn background
    # threads and has been observed to crash on Windows in CI/dev environments.
    if os.environ.get('PYTEST_CURRENT_TEST'):
        return True
    if 'pytest' in sys.modules:
        return True
    return False


def get_video_duration(video_path):
    """Get video duration using mutagen or fallback methods
    
    Returns duration in seconds as a float, or None if unable to determine
    """
    if not os.path.exists(video_path):
        return None
    
    # Try using mutagen (MP4 class handles MP4, M4V, and other MP4-based video containers)
    if MUTAGEN_AVAILABLE:
        try:
            video = MP4(video_path)
            if video.info and hasattr(video.info, 'length'):
                duration = video.info.length
                if duration is not None and duration > 0:
                    return float(duration)
        except MP4StreamInfoError as e:
            logger.debug(f"Mutagen MP4 stream error for {video_path}: {e}")
        except Exception as e:
            logger.debug(f"Mutagen failed to extract duration from {video_path}: {e}")
    
    # Fallback: Try using MPV in a temporary instance
    if MPV_AVAILABLE and not _running_under_pytest():
        temp_player = None
        try:
            temp_player = mpv.MPV(video=False, audio=False)
            temp_player.play(video_path)
            temp_player.wait_until_playing()
            duration = temp_player.duration
            if duration:
                return float(duration)
        except Exception as e:
            # MPV can raise various exceptions depending on the error
            # (MPVError, SystemError, etc.). Catch all to ensure robustness.
            logger.debug(f"MPV duration extraction failed for {video_path}: {e}")
        finally:
            if temp_player:
                try:
                    temp_player.terminate()
                except Exception:
                    # Ignore all cleanup errors
                    pass
    
    return None


class VideoPlaybackController:
    """Controls video playback with server-side rendering using mpv"""
    
    # Default configuration
    DEFAULT_VOLUME = 50  # Volume as integer 0-100
    DURATION_DETECTION_TIMEOUT = 2  # Seconds to wait for duration during playback
    
    def __init__(self, video_config=None, stats_manager=None, db_manager=None):
        self.current_playlist = []
        self.original_playlist = []  # Store original order for shuffle
        self.current_track_index = 0
        self.is_playing = False
        self.is_paused = False
        self.volume = self.DEFAULT_VOLUME  # Volume as integer 0-100
        self.current_position = 0  # Current playback position in seconds
        
        # Shuffle and repeat modes
        self.shuffle_enabled = False
        self.repeat_mode = 'none'  # 'none', 'all', 'one'

        # Audio/subtitle track selection
        # MPV uses 'aid' (audio) and 'sid' (subtitle) properties.
        # For subtitles, MPV supports disabling via 'no'. We represent "off" as -1 in the API.
        self.selected_audio_track_id = None
        self.selected_subtitle_track_id = -1
        self._audio_track_user_selected = False
        self._subtitle_track_user_selected = False

        # Per-user preference (set by app from session)
        # Values currently supported: 'deu', 'eng'
        self.current_user_preferred_language = 'eng'
        
        # Track timing state
        self.track_custom_start = None  # Custom start time in track (seconds)
        self.track_custom_end = None  # Custom end time in track (seconds)

        # Guard to prevent repeated end-time triggers per track
        self._custom_end_time_triggered = False
        
        # Video configuration
        self.video_config = video_config or {
            'fullscreen': True,
            'preferred_screen': None
        }

        # Optional unified cache DB (DatabaseManager). When present, playlist
        # entries are enriched from cached metadata to keep titles consistent
        # with library views.
        self.db = db_manager
        
        # MPV player instance
        self.player = None
        self.video_available = False
        
        # Stats tracking
        self.stats_manager = stats_manager
        self.current_username = None  # Set by app when playback starts
        self.stats_recorded = False  # Track if stats have been recorded for current track
        self.track_start_time = None  # System time when track started
        self.pause_start_time = None  # System time when paused
        self.total_pause_duration = 0  # Total time spent paused
        
        # Flag to prevent end-file event handling during manual operations
        self._manual_track_change = False
        
        # Initialize mpv if available (skip during unit tests)
        if MPV_AVAILABLE and not _running_under_pytest():
            self._initialize_mpv_player()
        else:
            logger.warning("python-mpv not installed, running in no-video mode")
    
    def _build_mpv_params(self):
        """Build MPV initialization parameters from current config
        
        Returns:
            Dictionary of MPV initialization parameters
        """
        mpv_params = {
            'input_default_bindings': True,
            'input_vo_keyboard': True,
            'osc': True,  # On-screen controller
            'ytdl': False,  # Don't use youtube-dl
            'fullscreen': self.video_config.get('fullscreen', True),
        }
        
        # Add screen selection if specified
        preferred_screen = self.video_config.get('preferred_screen')
        if preferred_screen is not None:
            # mpv distinguishes between window placement (--screen/--screen-name)
            # and which monitor to use for fullscreen (--fs-screen/--fs-screen-name).
            # We set both so it behaves as users expect when fullscreen is enabled.
            screen_value = preferred_screen
            if isinstance(screen_value, str):
                screen_str = screen_value.strip()
                # Accept numeric strings from JSON/UI.
                if screen_str.isdigit() or (screen_str.startswith('-') and screen_str[1:].isdigit()):
                    screen_value = int(screen_str)
                else:
                    mpv_params['screen_name'] = screen_str
                    mpv_params['fs_screen_name'] = screen_str
                    screen_value = None

            if screen_value is not None:
                mpv_params['screen'] = screen_value
                mpv_params['fs_screen'] = screen_value
        logger.info(f"MPV parameters: {mpv_params}")
        
        return mpv_params
    
    def _setup_mpv_event_handlers(self):
        """Setup event handlers for MPV player"""
        if not self.player:
            return
        
        @self.player.property_observer('time-pos')
        def time_observer(_name, value):
            if value is not None:
                self.current_position = value
                # Check if we should record stats
                self._check_and_record_stats()
                # Enforce per-track custom end time if configured
                self._check_custom_end_time()
        
        @self.player.event_callback('end-file')
        def end_file_callback(_event):
            # _event parameter intentionally unused
            # Only handle video end if this wasn't a manual track change
            if not self._manual_track_change:
                logger.info("Video ended, playing next")
                self._handle_video_end()
            else:
                logger.debug("Ignoring end-file event during manual track change")
                # Reset the flag after ignoring the event
                self._manual_track_change = False
    
    def _initialize_mpv_player(self):
        """Initialize or reinitialize the MPV player with current config"""
        try:
            mpv_params = self._build_mpv_params()
            self.player = mpv.MPV(**mpv_params)
            self._setup_mpv_event_handlers()
            self.video_available = True
            logger.info("MPV player initialized successfully")
        except Exception as e:
            logger.warning(f"Video player initialization failed: {e}")
            print(f"Running in no-video mode: {e}")
            self.video_available = False
    
    def __del__(self):
        """Cleanup MPV player on deletion
        
        Note: __del__ is not guaranteed to be called in Python.
        Use cleanup() method for reliable resource cleanup.
        This is provided as a best-effort fallback only.
        """
        if self.player:
            try:
                self.player.terminate()
                # Note: Not setting self.player = None here as this is
                # best-effort cleanup in __del__. Use cleanup() for full cleanup.
                logger.info("MPV player terminated in __del__")
            except Exception as e:
                logger.debug(f"Error terminating MPV player in __del__: {e}")
    
    def cleanup(self):
        """Explicitly cleanup MPV player resources
        
        This is the recommended way to cleanup resources.
        Call this method explicitly when done with the controller.
        """
        if self.player:
            try:
                self.player.terminate()
                self.player = None
                self.video_available = False
                logger.info("Video player cleaned up")
            except Exception as e:
                logger.error(f"Error cleaning up video player: {e}")
    
    def update_video_config(self, config):
        """Update video configuration settings
        
        Note: Changes to screen and fullscreen settings require restarting
        the MPV player instance to take effect. This method will reinitialize
        the player if it's available and MPV is installed.
        
        Args:
            config: Dictionary with video configuration options
                   - fullscreen: boolean
                   - preferred_screen: int, string, or None
        """
        if config:
            self.video_config.update(config)
            logger.info(f"Video config updated: {self.video_config}")
            
            # Reinitialize MPV player to apply new settings
            if MPV_AVAILABLE:
                was_playing = self.is_playing
                current_index = self.current_track_index
                
                # Clean up existing player
                if self.player:
                    try:
                        self.player.terminate()
                    except Exception as e:
                        logger.debug(f"Error terminating player during config update: {e}")
                
                # Reinitialize with new settings using helper method
                self._initialize_mpv_player()
                
                # Resume playback if it was playing before
                if was_playing and self.current_playlist and self.video_available:
                    self.current_track_index = current_index
                    self.play()
    
    def get_video_config(self):
        """Get current video configuration"""
        return self.video_config.copy()
    
    def _handle_video_end(self):
        """Handle video end event"""
        if self.repeat_mode == 'one':
            # Replay current video
            self.play()
        else:
            # Move to next video (next_track handles end-of-playlist logic)
            if not self.next_track():
                # If next_track returns False, we've reached the end
                logger.info("Playlist completed, stopping playback")

    @staticmethod
    def _ms_to_seconds(value):
        """Convert a ms-like value (int/float/numeric str) to seconds float."""
        if value is None:
            return None
        if isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            return float(value) / 1000.0
        if isinstance(value, str):
            s = value.strip()
            if not s:
                return None
            try:
                return float(s) / 1000.0
            except ValueError:
                return None
        return None

    def _get_custom_times_for_path(self, video_path: str, cached: dict | None = None):
        """Get custom start/end times (seconds) for a given video file path."""
        try:
            if cached is None and self.db is not None:
                cached = self.db.get_cached_video_by_path(video_path)
        except Exception:
            cached = None

        if isinstance(cached, dict):
            start_sec = self._ms_to_seconds(cached.get('start_time_in_ms'))
            end_sec = self._ms_to_seconds(cached.get('end_time_in_ms'))

            # Sanity: ignore negatives
            if start_sec is not None and start_sec < 0:
                start_sec = None
            if end_sec is not None and end_sec < 0:
                end_sec = None
            # If end <= start, treat as invalid
            if start_sec is not None and end_sec is not None and end_sec <= start_sec:
                end_sec = None

            if start_sec is not None or end_sec is not None:
                return start_sec, end_sec

        try:
            metadata = read_video_metadata(
                video_path,
                include_duration=False,
                check_nfo=True,
                include_thumbnail=False,
            )
        except Exception:
            return None, None

        start_sec = self._ms_to_seconds(metadata.get('start_time_in_ms'))
        end_sec = self._ms_to_seconds(metadata.get('end_time_in_ms'))

        # Sanity: ignore negatives
        if start_sec is not None and start_sec < 0:
            start_sec = None
        if end_sec is not None and end_sec < 0:
            end_sec = None
        # If end <= start, treat as invalid
        if start_sec is not None and end_sec is not None and end_sec <= start_sec:
            end_sec = None

        return start_sec, end_sec

    @staticmethod
    def _stable_media_id_for_path(video_path: str) -> str | None:
        if not isinstance(video_path, str) or not video_path.strip():
            return None
        normalized_path = os.path.normpath(video_path)
        return hashlib.sha256(normalized_path.encode('utf-8', errors='replace')).hexdigest()

    def _build_track_entry(self, track_path: str, *, extinf_title: str | None = None, cached: dict | None = None):
        """Build a playlist entry enriched with DB metadata when possible."""
        if not os.path.exists(track_path):
            return None

        if cached is None and self.db is not None:
            try:
                cached = self.db.get_cached_video_by_path(track_path)
            except Exception:
                cached = None

        # Duration: prefer cached duration to avoid external probing.
        duration = None
        if isinstance(cached, dict):
            try:
                dur = cached.get('duration')
                if dur is not None:
                    dur = float(dur)
                if dur and dur > 0:
                    duration = dur
            except Exception:
                duration = None
        if duration is None:
            duration = get_video_duration(track_path)

        # Title: prefer cached DB title (from NFO/embedded tags), else scrape, else EXTINF, else filename.
        title = None
        artist = None
        tags = None
        media_id = None
        has_thumbnail = None
        thumbnail_url = None

        if isinstance(cached, dict):
            media_id = cached.get('media_id')
            title = cached.get('title')
            artist = cached.get('artist')
            tags = cached.get('tags')
            has_thumbnail = cached.get('has_thumbnail')
            thumbnail_url = cached.get('thumbnail_url')

        if not isinstance(title, str) or not title.strip():
            try:
                scraped = read_video_metadata(
                    track_path,
                    include_duration=False,
                    check_nfo=True,
                    include_thumbnail=False,
                )
            except Exception:
                scraped = {}

            scraped_title = scraped.get('title')
            if isinstance(scraped_title, str) and scraped_title.strip():
                title = scraped_title.strip()
            scraped_artist = scraped.get('artist')
            if (artist is None) and isinstance(scraped_artist, str) and scraped_artist.strip():
                artist = scraped_artist.strip()
            scraped_tags = scraped.get('tags')
            if tags is None and isinstance(scraped_tags, list):
                tags = scraped_tags

        if not isinstance(title, str) or not title.strip():
            if isinstance(extinf_title, str) and extinf_title.strip():
                title = extinf_title.strip()
            else:
                title = os.path.splitext(os.path.basename(track_path))[0]

        if not isinstance(media_id, str) or not media_id.strip():
            media_id = self._stable_media_id_for_path(track_path)

        start_time, end_time = self._get_custom_times_for_path(track_path, cached=cached if isinstance(cached, dict) else None)

        entry = {
            'path': track_path,
            'title': title,
            'duration': duration,
            'start_time': start_time,
            'end_time': end_time,
            'media_id': media_id,
        }

        if isinstance(artist, str) and artist.strip():
            entry['artist'] = artist.strip()
        if isinstance(tags, list):
            entry['tags'] = tags
        if has_thumbnail is not None:
            entry['has_thumbnail'] = bool(has_thumbnail)
        if isinstance(thumbnail_url, str) and thumbnail_url.strip():
            entry['thumbnail_url'] = thumbnail_url.strip()

        return entry

    def _check_custom_end_time(self):
        """If the current track has an end_time, auto-advance when reached."""
        if not self.is_playing or self.is_paused:
            return

        current_track = self.get_current_track()
        if not current_track:
            return

        end_time = current_track.get('end_time')
        if end_time is None:
            return

        try:
            end_time = float(end_time)
        except (TypeError, ValueError):
            return

        # Rearm if user seeks back below end time.
        if self.current_position < max(0.0, end_time - 0.25):
            self._custom_end_time_triggered = False

        if self._custom_end_time_triggered:
            return

        if self.current_position >= end_time:
            self._custom_end_time_triggered = True
            logger.info(f"Custom end time reached ({end_time:.3f}s), advancing to next video")
            self._handle_video_end()
    
    def load_playlist(self, playlist_path, track_index=0):
        """Load a video playlist from an M3U file"""
        if not os.path.exists(playlist_path):
            logger.error(f"Playlist not found: {playlist_path}")
            return False
        
        playlist_dir = os.path.dirname(playlist_path)
        tracks = []

        # Preload cached metadata for absolute paths when possible.
        cached_by_path = {}
        if self.db is not None:
            try:
                # Best-effort: collect paths (including relative candidates) first.
                with open(playlist_path, 'r', encoding='utf-8-sig') as f:
                    raw_lines = [ln.strip() for ln in f.readlines()]

                candidate_paths = []
                extinf_title = None
                for line in raw_lines:
                    if not line:
                        continue
                    if line.startswith('#'):
                        if line.startswith('#EXTINF:'):
                            parts = line[8:].split(',', 1)
                            extinf_title = parts[1].strip() if len(parts) == 2 else None
                        continue

                    # Normalize Windows path separators in M3U (non-URL).
                    if '://' not in line:
                        line = line.replace('\\\\', '/').replace('\\', '/')

                    if os.path.isabs(line):
                        candidate_paths.append(os.path.normpath(line))
                    else:
                        candidate_paths.append(os.path.normpath(os.path.join(playlist_dir, line)))

                cached_by_path = self.db.get_videos_by_paths(candidate_paths)
            except Exception:
                cached_by_path = {}

        try:
            with open(playlist_path, 'r', encoding='utf-8-sig') as f:
                extinf_title = None
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith('#'):
                        if line.startswith('#EXTINF:'):
                            parts = line[8:].split(',', 1)
                            extinf_title = parts[1].strip() if len(parts) == 2 else None
                        continue

                    # Normalize Windows path separators in M3U (non-URL).
                    if '://' not in line:
                        line = line.replace('\\\\', '/').replace('\\', '/')

                    if os.path.isabs(line):
                        track_path = os.path.normpath(line)
                    else:
                        track_path = os.path.normpath(os.path.join(playlist_dir, line))

                    cached = cached_by_path.get(os.path.normpath(track_path)) if isinstance(cached_by_path, dict) else None
                    entry = self._build_track_entry(track_path, extinf_title=extinf_title, cached=cached)
                    extinf_title = None
                    if entry:
                        tracks.append(entry)

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

        # If shuffle is already enabled, apply it to the newly loaded playlist.
        # When starting a playlist from the Playlists page we typically start at track_index=0,
        # and users expect the first track to be random as well.
        if self.shuffle_enabled and self.current_playlist:
            if self.current_track_index != 0:
                current_track = self.current_playlist[self.current_track_index]
                remaining_tracks = [
                    t for i, t in enumerate(self.current_playlist)
                    if i != self.current_track_index
                ]
                random.shuffle(remaining_tracks)
                self.current_playlist = [current_track] + remaining_tracks
            else:
                random.shuffle(self.current_playlist)

            self.current_track_index = 0
        
        logger.info(f"Loaded playlist with {len(tracks)} videos")
        return True
    
    def add_tracks(self, track_paths):
        """Add tracks to the current playlist and auto-start if not playing"""
        valid_tracks_added = 0
        was_empty = len(self.current_playlist) == 0

        cached_by_path = {}
        if self.db is not None:
            try:
                cached_by_path = self.db.get_videos_by_paths(track_paths)
            except Exception:
                cached_by_path = {}
        
        for path in track_paths:
            norm = os.path.normpath(path) if isinstance(path, str) else path
            cached = cached_by_path.get(norm) if isinstance(cached_by_path, dict) else None
            entry = self._build_track_entry(path, cached=cached)
            if entry:
                self.current_playlist.append(entry)
                valid_tracks_added += 1
        
        if not self.original_playlist:
            self.original_playlist = copy.deepcopy(self.current_playlist)
        
        # Auto-start playback if playlist was empty, videos were added, and not currently playing/paused
        if was_empty and valid_tracks_added > 0 and not self.is_playing and not self.is_paused:
            logger.info(f"Auto-starting playback after adding {valid_tracks_added} video(s)")
            self.play()
        
        return True

    def play_single_video(self, video_path: str) -> bool:
        """Replace the current playlist with a single video and start playback."""
        if not isinstance(video_path, str) or not video_path.strip():
            return False

        if not os.path.exists(video_path):
            return False

        # Stop current playback (does not clear playlist).
        self.stop()

        # Replace playlist with just this one video.
        self.current_playlist = []
        self.original_playlist = []
        self.current_track_index = 0
        self.current_position = 0

        self.add_tracks([video_path])

        # Ensure playback is started (add_tracks auto-starts only in specific cases).
        if self.current_playlist and not self.is_playing and not self.is_paused:
            self.play()

        return bool(self.current_playlist)
    
    def pause(self):
        """Pause playback"""
        if self.is_playing and not self.is_paused:
            if self.player and self.video_available:
                try:
                    self.player.pause = True
                    logger.info("Video paused")
                except Exception as e:
                    logger.error(f"Error pausing video: {e}")
            
            self.is_paused = True
            self.pause_start_time = time.time()  # Track when pause started
            return True
        return False
    
    def play(self):
        """Start or resume playback"""
        if not self.current_playlist:
            logger.warning("Cannot play: no playlist loaded")
            return False
        
        current_track = self.get_current_track()
        if not current_track:
            logger.warning("No current track to play")
            return False
        
        # If already playing and paused, just resume
        if self.is_paused and self.player and self.video_available:
            try:
                self.player.pause = False
                self.is_paused = False
                # Track pause duration
                if self.pause_start_time is not None:
                    self.total_pause_duration += time.time() - self.pause_start_time
                    self.pause_start_time = None
                logger.info("Resumed video playback")
                return True
            except Exception as e:
                logger.error(f"Error resuming video: {e}")
        
        # Start new video playback
        if self.player and self.video_available:
            try:
                video_path = current_track['path']
                if not os.path.exists(video_path):
                    logger.error(f"Video file not found: {video_path}")
                    return False
                
                # Stop any currently playing video
                if self.is_playing:
                    # Prevent stop() from triggering an end-file -> next-track chain.
                    self._manual_track_change = True
                    self.player.stop()
                
                # Load and play the video
                self.player.play(video_path)

                # Best-effort: choose a preferred-language audio track if multiple are available
                # and the user hasn't explicitly picked an audio track.
                try:
                    self._maybe_select_default_audio_track()
                except Exception as e:
                    logger.debug(f"Error selecting default audio track: {e}")

                # Best-effort: apply stored audio/subtitle selection.
                try:
                    self._apply_selected_tracks_to_player()
                except Exception as e:
                    logger.debug(f"Error applying audio/subtitle track selection: {e}")

                # Best-effort: if subtitles are currently off and we haven't explicitly
                # selected a subtitle track yet, auto-enable a matching "forced" subtitle.
                try:
                    self._maybe_select_default_forced_subtitle()
                except Exception as e:
                    logger.debug(f"Error selecting default forced subtitle: {e}")

                # Reset end-time trigger guard for this track
                self._custom_end_time_triggered = False
                
                # Set volume (don't fail playback if this errors)
                try:
                    self.player.volume = self.volume
                except Exception as e:
                    logger.debug(f"Error setting MPV volume: {e}")

                # Apply custom start time if set (must be positive).
                # MPV may reject seeks until the file is actually loaded/playing.
                start_time = current_track.get('start_time')
                if start_time is not None:
                    try:
                        start_time = float(start_time)
                    except (TypeError, ValueError):
                        start_time = None

                if start_time is not None and start_time > 0:
                    try:
                        self.player.wait_until_playing(timeout=self.DURATION_DETECTION_TIMEOUT)
                    except Exception as e:
                        logger.debug(f"MPV not ready for seek yet: {e}")
                    try:
                        self.player.seek(start_time, reference='absolute')
                    except Exception as e:
                        logger.debug(f"Error seeking to custom start time {start_time}s: {e}")
                
                self.is_playing = True
                self.is_paused = False
                self.stats_recorded = False  # Reset stats flag for new video
                self.track_start_time = time.time()  # Set start time for stats tracking
                self.pause_start_time = None
                self.total_pause_duration = 0
                
                # Try to get duration from MPV if not already available
                if current_track.get('duration') is None:
                    try:
                        # Wait a moment for video to load
                        self.player.wait_until_playing(timeout=self.DURATION_DETECTION_TIMEOUT)
                        if self.player.duration:
                            current_track['duration'] = float(self.player.duration)
                            logger.info(f"Got duration from MPV: {current_track['duration']}s")
                    except Exception as e:
                        # MPV operations can raise various exceptions
                        logger.debug(f"Could not get duration from MPV: {e}")
                
                logger.info(f"Playing video {self.current_track_index + 1}/{len(self.current_playlist)}: {video_path}")
                return True
            except Exception as e:
                logger.error(f"Error playing video: {e}")
                return False
        else:
            # No video player available, just update state
            self.is_playing = True
            self.is_paused = False
            # Reset end-time trigger guard for this track
            self._custom_end_time_triggered = False
            logger.info(f"Video playback state updated (no player available)")
            return True

    def _get_mpv_track_list(self):
        """Return MPV track-list as a list of dicts, or empty list on failure."""
        if not self.player or not self.video_available:
            return []
        try:
            track_list = getattr(self.player, 'track_list', None)
            if track_list is None:
                return []
            if not isinstance(track_list, (list, tuple)):
                return []
            tracks = [t for t in track_list if isinstance(t, dict)]
            return tracks
        except Exception:
            return []

    @staticmethod
    def _format_track_label(track_type: str, track_id: int, title, lang) -> str:
        """Create a stable, human-friendly label for track selectors.

        Preferred format: "title - lang (id)".
        If title/lang are missing, fall back gracefully.
        """
        title_str = str(title).strip() if isinstance(title, str) else ''
        lang_str = str(lang).strip() if isinstance(lang, str) else ''

        if title_str and lang_str:
            return f"{title_str} - {lang_str} ({track_id})"
        if title_str:
            return f"{title_str} ({track_id})"
        if lang_str:
            return f"{lang_str} ({track_id})"
        return f"{track_type} {track_id}"

    @staticmethod
    def _get_track_title_from_mpv_track(track_dict: dict):
        title = track_dict.get('title')
        if isinstance(title, str) and title.strip():
            return title

        metadata = track_dict.get('metadata')
        if isinstance(metadata, dict):
            name = metadata.get('name')
            if isinstance(name, str) and name.strip():
                return name

        return None

    @staticmethod
    def _text_contains_forced(text) -> bool:
        if not isinstance(text, str):
            return False
        return 'forced' in text.lower()

    def set_current_user_preferred_language(self, preferred_language: str | None) -> None:
        if not isinstance(preferred_language, str) or not preferred_language.strip():
            self.current_user_preferred_language = 'eng'
            return
        self.current_user_preferred_language = preferred_language.strip().lower()

    @staticmethod
    def _normalize_language(lang: str) -> str:
        return lang.strip().lower()

    @staticmethod
    def _preferred_language_aliases(preferred_language: str):
        pref = (preferred_language or '').strip().lower()
        aliases = {pref}
        # Map ISO-639-2/3 preferences to common ISO-639-1 codes seen in some files.
        if pref == 'eng':
            aliases.add('en')
        if pref == 'deu':
            aliases.add('de')
            aliases.add('ger')
        return aliases

    @staticmethod
    def _track_is_visual_impaired(track_dict: dict) -> bool:
        # MPV key names can include hyphens; tolerate both styles.
        val = track_dict.get('visual-impaired')
        if val is None:
            val = track_dict.get('visual_impaired')
        return bool(val)

    def _maybe_select_default_audio_track(self) -> None:
        """Auto-select an audio track matching the user's preferred language.

        Rule:
        - If multiple audio tracks exist, try to select one matching the user's preferred language.
        - If multiple match, prefer the one that is NOT visual-impaired.
        - Never override if user explicitly selected an audio track via the API/UI.
        """
        logger.debug("Attempting to auto-select default audio track based on user preference")
        if not self.player or not self.video_available:
            return

        if self._audio_track_user_selected:
            return

        # MPV may not have parsed tracks immediately after play(); wait briefly.
        tracks = self._get_mpv_track_list()
        if not tracks:
            # Best-effort: wait for playback to start, then re-check track list.
            try:
                if hasattr(self.player, 'wait_until_playing'):
                    self.player.wait_until_playing(timeout=0.75)
            except Exception:
                pass

            deadline = time.time() + 0.75
            while time.time() < deadline and not tracks:
                time.sleep(0.05)
                tracks = self._get_mpv_track_list()

        if not tracks:
            return

        audio_tracks = []
        for t in tracks:
            if t.get('type') != 'audio':
                continue
            tid = t.get('id')
            if not isinstance(tid, int):
                continue
            lang = t.get('lang')
            audio_tracks.append({
                'id': tid,
                'lang': lang if isinstance(lang, str) else None,
                'visual_impaired': self._track_is_visual_impaired(t),
                'selected': bool(t.get('selected')),
            })

        if len(audio_tracks) < 2:
            return

        aliases = self._preferred_language_aliases(self.current_user_preferred_language)
        candidates = []
        for t in audio_tracks:
            lang = t.get('lang')
            if not isinstance(lang, str) or not lang.strip():
                continue
            lang_norm = self._normalize_language(lang)
            if lang_norm in aliases:
                candidates.append(t)

        if not candidates:
            return

        non_vi = [t for t in candidates if not t.get('visual_impaired')]
        preferred_set = non_vi if non_vi else candidates

        # Prefer MPV's currently-selected track if it's in our preferred set.
        current_aid = self._get_current_aid()
        if isinstance(current_aid, int):
            for t in preferred_set:
                if t['id'] == current_aid:
                    self.selected_audio_track_id = current_aid
                    try:
                        self.player.aid = int(current_aid)
                    except Exception:
                        pass
                    return

        chosen = sorted(preferred_set, key=lambda x: x['id'])[0]
        self.selected_audio_track_id = int(chosen['id'])
        try:
            self.player.aid = int(chosen['id'])
        except Exception:
            pass

    def _maybe_select_default_forced_subtitle(self):
        """Auto-select a matching forced subtitle if subtitles are off.

        Rule:
        - If subtitle title (or metadata.name) contains "forced" AND subtitle language matches
          the active audio track language, enable that subtitle by default.
        - Only do this when subtitles are currently off and user hasn't explicitly selected
          a subtitle track via the API/UI.
        """
        if not self.player or not self.video_available:
            return

        if self._subtitle_track_user_selected:
            return

        current_sid = self._get_current_sid()
        sid_is_off = current_sid in (None, 'no', 'disabled', False)
        if not sid_is_off:
            return

        # Ensure we have an audio language to compare against.
        tracks = self._get_mpv_track_list()
        if not tracks:
            return

        current_aid = self._get_current_aid()
        audio_lang = None
        if isinstance(current_aid, int):
            for t in tracks:
                if t.get('type') == 'audio' and t.get('id') == current_aid:
                    audio_lang = t.get('lang')
                    break
        if not isinstance(audio_lang, str) or not audio_lang.strip():
            # Fallback: whichever audio track MPV marks as selected.
            for t in tracks:
                if t.get('type') == 'audio' and bool(t.get('selected')):
                    audio_lang = t.get('lang')
                    break

        if not isinstance(audio_lang, str) or not audio_lang.strip():
            return
        audio_lang_norm = audio_lang.strip().lower()

        candidates = []
        for t in tracks:
            if t.get('type') != 'sub':
                continue
            tid = t.get('id')
            if not isinstance(tid, int):
                continue
            sub_lang = t.get('lang')
            if not isinstance(sub_lang, str) or not sub_lang.strip():
                continue
            if sub_lang.strip().lower() != audio_lang_norm:
                continue

            title = t.get('title')
            meta_name = None
            metadata = t.get('metadata')
            if isinstance(metadata, dict):
                meta_name = metadata.get('name')

            if self._text_contains_forced(title) or self._text_contains_forced(meta_name) or t.get('forced'):
                candidates.append(tid)

        if not candidates:
            return

        chosen_id = sorted(candidates)[0]
        self.selected_subtitle_track_id = chosen_id
        try:
            self.player.sid = int(chosen_id)
        except Exception as e:
            logger.debug(f"Failed to set MPV sid={chosen_id} for forced subtitle default: {e}")

    def _get_track_options(self, track_type: str):
        tracks = self._get_mpv_track_list()
        options = []
        for t in tracks:
            if t.get('type') != track_type:
                continue
            tid = t.get('id')
            if not isinstance(tid, int):
                continue
            title = self._get_track_title_from_mpv_track(t)
            lang = t.get('lang')
            label = self._format_track_label(track_type, tid, title, lang)
            options.append({
                'id': tid,
                'label': label,
                'title': title if isinstance(title, str) and title.strip() else None,
                'lang': lang if isinstance(lang, str) and lang.strip() else None,
                'selected': bool(t.get('selected')),
            })
        return options

    def _get_current_aid(self):
        if self.player and self.video_available:
            try:
                val = getattr(self.player, 'aid', None)
                return val
            except Exception:
                return None
        return None

    def _get_current_sid(self):
        if self.player and self.video_available:
            try:
                val = getattr(self.player, 'sid', None)
                return val
            except Exception:
                return None
        return None

    def _apply_selected_tracks_to_player(self):
        if not self.player or not self.video_available:
            return

        # Audio
        if isinstance(self.selected_audio_track_id, int) and self.selected_audio_track_id >= 0:
            try:
                self.player.aid = int(self.selected_audio_track_id)
            except Exception as e:
                logger.debug(f"Failed to set MPV aid={self.selected_audio_track_id}: {e}")

        # Subtitles
        if isinstance(self.selected_subtitle_track_id, int):
            try:
                if self.selected_subtitle_track_id < 0:
                    self.player.sid = 'no'
                else:
                    self.player.sid = int(self.selected_subtitle_track_id)
            except Exception as e:
                logger.debug(f"Failed to set MPV sid={self.selected_subtitle_track_id}: {e}")

    def set_audio_track(self, track_id):
        """Select an audio track by MPV track id."""
        try:
            tid = int(track_id)
        except Exception:
            return False

        if tid < 0:
            return False

        self.selected_audio_track_id = tid
        self._audio_track_user_selected = True
        if self.player and self.video_available:
            try:
                self.player.aid = tid
            except Exception as e:
                logger.debug(f"Error setting audio track: {e}")
                return False
        return True

    def set_subtitle_track(self, track_id):
        """Select a subtitle track by MPV track id, or disable with -1."""
        try:
            tid = int(track_id)
        except Exception:
            return False

        self.selected_subtitle_track_id = tid
        self._subtitle_track_user_selected = True
        if self.player and self.video_available:
            try:
                if tid < 0:
                    self.player.sid = 'no'
                else:
                    self.player.sid = tid
            except Exception as e:
                logger.debug(f"Error setting subtitle track: {e}")
                return False
        return True
    
    def _check_and_record_stats(self):
        """Check if playback has reached the threshold for recording stats"""
        if self.stats_recorded or not self.stats_manager or not self.current_username:
            return
        
        if not self.stats_manager.is_initialized():
            return
        
        if not self.current_playlist or self.current_track_index >= len(self.current_playlist):
            return
        
        current_track = self.current_playlist[self.current_track_index]
        video_path = current_track.get('path')
        
        if not video_path or not self.track_start_time:
            return
        
        # Get video duration
        duration = current_track.get('duration')
        if duration is None or duration <= 0:
            return
        
        # Calculate elapsed playback time (excluding paused time)
        elapsed = time.time() - self.track_start_time - self.total_pause_duration
        
        # Determine the effective duration considering custom start/end times
        # Note: keys may exist with value None; coerce None to defaults
        start_time_val = current_track.get('start_time')
        end_time_val = current_track.get('end_time')
        effective_start = start_time_val if start_time_val is not None else 0
        effective_end = end_time_val if end_time_val is not None else duration
        effective_duration = effective_end - effective_start
        
        if effective_duration <= 0:
            return
        
        # Calculate thresholds: 50% or 5 minutes (300 seconds), whichever is smaller
        threshold = min(effective_duration * 0.5, 300.0)
        
        if elapsed >= threshold:
            # Record the stat
            try:
                # Get the full path with correct casing and record it
                actual_path = get_actual_path_with_correct_case(video_path)
                if self.stats_manager.record_media_stat(
                    actual_path,
                    self.current_username,
                    media_id=current_track.get('media_id'),
                ):
                    self.stats_recorded = True
                    logger.info(f"Recorded stats for {video_path} (played {elapsed:.1f}s of {effective_duration:.1f}s)")
            except Exception as e:
                logger.error(f"Failed to record stats: {e}")

    def stop(self):
        """Stop playback"""
        if self.player and self.video_available:
            try:
                self.player.stop()
                logger.info("Video stopped")
            except Exception as e:
                logger.error(f"Error stopping video: {e}")
        
        self.is_playing = False
        self.is_paused = False
        self.current_position = 0
        return True

    def clear_playlist(self):
        """Clear the current playlist/queue without changing user settings.

        This resets the currently loaded playlist and related per-track state.
        It does not change volume, shuffle, or repeat settings.
        """
        self.current_playlist = []
        self.original_playlist = []
        self.current_track_index = 0
        self.current_position = 0

        # Reset per-track timing state
        self.track_custom_start = None
        self.track_custom_end = None
        self._custom_end_time_triggered = False

        # Reset stats state
        self.current_username = None
        self.stats_recorded = False
        self.track_start_time = None
        self.pause_start_time = None
        self.total_pause_duration = 0

    def stop_and_clear_playlist(self):
        """Stop playback and clear the current playlist/queue."""
        self.stop()
        self.clear_playlist()
        return True
    
    def next_track(self):
        """Skip to next track"""
        if not self.current_playlist:
            return False
        
        # Set flag to prevent end-file event from triggering during manual skip
        self._manual_track_change = True
        
        if self.current_track_index < len(self.current_playlist) - 1:
            self.current_track_index += 1
            self.current_position = 0
            logger.info(f"Skipped to next video: {self.current_track_index + 1}/{len(self.current_playlist)}")
            # Auto-play next video if currently playing
            if self.is_playing:
                self.play()
            return True
        elif self.repeat_mode == 'all':
            self.current_track_index = 0
            self.current_position = 0
            logger.info("Playlist ended, repeating from start")
            # Auto-play first video if currently playing
            if self.is_playing:
                self.play()
            return True
        else:
            logger.info("Reached end of playlist")
            self.stop()
            return False
    
    def previous_track(self):
        """Skip to previous track"""
        if not self.current_playlist:
            return False
        
        # Set flag to prevent end-file event from triggering during manual skip
        self._manual_track_change = True
        
        if self.current_track_index > 0:
            self.current_track_index -= 1
            self.current_position = 0
            logger.info(f"Skipped to previous video: {self.current_track_index + 1}/{len(self.current_playlist)}")
            # Auto-play previous video if currently playing
            if self.is_playing:
                self.play()
            return True
        return False
    
    def set_volume(self, volume):
        """Set playback volume (0-100)"""
        self.volume = max(0, min(100, int(volume)))
        
        if self.player and self.video_available:
            try:
                self.player.volume = self.volume
                logger.info(f"Volume set to {self.volume}%")
            except Exception as e:
                logger.error(f"Error setting volume: {e}")
        else:
            logger.info(f"Volume set to {self.volume}% (no player available)")
        
        return True
    
    def seek(self, position):
        """Seek to a specific position in seconds"""
        self.current_position = max(0, position)
        
        if self.player and self.video_available and self.is_playing:
            try:
                self.player.seek(position, reference='absolute')
                logger.info(f"Seeked to position {position}s")
            except Exception as e:
                logger.error(f"Error seeking: {e}")
        else:
            logger.info(f"Seek position set to {position}s (no active player)")
        
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

        audio_tracks = self._get_track_options('audio')
        subtitle_tracks = self._get_track_options('sub')

        # Prepend an "Off" option for subtitles when subtitle tracks exist.
        if subtitle_tracks:
            current_sid = self._get_current_sid()
            sid_is_off = current_sid in (None, 'no', 'disabled', False)
            off_selected = sid_is_off or (isinstance(self.selected_subtitle_track_id, int) and self.selected_subtitle_track_id < 0)
            subtitle_tracks = [{'id': -1, 'label': 'Off', 'title': None, 'lang': None, 'selected': bool(off_selected)}] + subtitle_tracks

        current_aid = self._get_current_aid()
        current_sid = self._get_current_sid()

        current_audio_track_id = None
        if isinstance(current_aid, int):
            current_audio_track_id = current_aid
        elif isinstance(self.selected_audio_track_id, int):
            current_audio_track_id = self.selected_audio_track_id

        current_subtitle_track_id = None
        if isinstance(current_sid, int):
            current_subtitle_track_id = current_sid
        elif isinstance(current_sid, str) and current_sid.strip().lower() == 'no':
            current_subtitle_track_id = -1
        elif isinstance(self.selected_subtitle_track_id, int):
            current_subtitle_track_id = self.selected_subtitle_track_id
        
        return {
            'is_playing': self.is_playing,
            'is_paused': self.is_paused,
            'current_track': current_track,
            'next_track': next_track,
            'current_track_index': self.current_track_index,
            'playlist_length': len(self.current_playlist),
            'volume': self.volume,  # Volume as integer 0-100
            'shuffle': self.shuffle_enabled,
            'repeat_mode': self.repeat_mode,
            'current_position': self.current_position,
            'audio_tracks': audio_tracks,
            'subtitle_tracks': subtitle_tracks,
            'current_audio_track_id': current_audio_track_id,
            'current_subtitle_track_id': current_subtitle_track_id,
        }
    
    def get_playlist(self):
        """Get the current playlist"""
        return self.current_playlist
