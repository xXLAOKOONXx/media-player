"""Video Playback Controller

Handles video playback using python-vlc with support for audio/subtitle track selection.
"""

try:
    import vlc
    VLC_AVAILABLE = True
except ImportError:
    VLC_AVAILABLE = False
    print("Warning: python-vlc not available, running in simulation mode")

import os
from threading import Thread, Event
import time
import logging

# Configure logging
logger = logging.getLogger('VideoPlaybackController')
if not logger.handlers:
    logger.setLevel(logging.INFO)


class VideoPlaybackController:
    """Controls video playback with audio and subtitle track selection"""
    
    def __init__(self):
        self.video_available = False
        self.player = None
        self.instance = None
        
        if VLC_AVAILABLE:
            try:
                self.instance = vlc.Instance('--no-xlib')  # For headless server
                self.player = self.instance.media_player_new()
                self.video_available = True
                logger.info("VLC player initialized successfully")
            except Exception as e:
                logger.warning(f"VLC initialization failed: {e}")
                print("Running in no-video mode. Playback will be simulated.")
        else:
            logger.warning("python-vlc not installed, running in no-video mode")
        
        self.current_playlist = []
        self.current_index = 0
        self.state = 'stopped'  # stopped, playing, paused
        self.volume = 50
        
        # Audio and subtitle track info
        self.audio_tracks = []
        self.subtitle_tracks = []
        self.current_audio_track = 0
        self.current_subtitle_track = -1
        
        # Monitoring
        self.monitor_thread = None
        self.monitor_stop_event = Event()
    
    def load_playlist(self, playlist_path):
        """Load a playlist file"""
        try:
            if not os.path.exists(playlist_path):
                logger.error(f"Playlist not found: {playlist_path}")
                return False
            
            playlist_dir = os.path.dirname(playlist_path)
            self.current_playlist = []
            
            with open(playlist_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    # Handle relative paths
                    if not os.path.isabs(line):
                        line = os.path.join(playlist_dir, line)
                    
                    if os.path.exists(line):
                        self.current_playlist.append({
                            'path': line,
                            'name': os.path.basename(line),
                            'title': os.path.splitext(os.path.basename(line))[0]
                        })
            
            logger.info(f"Loaded playlist with {len(self.current_playlist)} videos")
            return True
            
        except Exception as e:
            logger.error(f"Error loading playlist: {e}")
            return False
    
    def play(self, video_path=None, track_index=0):
        """Start or resume playback"""
        if video_path:
            # Play specific video
            self.current_playlist = [{
                'path': video_path,
                'name': os.path.basename(video_path),
                'title': os.path.splitext(os.path.basename(video_path))[0]
            }]
            self.current_index = 0
        elif isinstance(track_index, int) and 0 <= track_index < len(self.current_playlist):
            self.current_index = track_index
        
        if not self.current_playlist:
            logger.error("No video to play")
            return False
        
        video_path = self.current_playlist[self.current_index]['path']
        
        if self.video_available and self.player:
            try:
                media = self.instance.media_new(video_path)
                self.player.set_media(media)
                self.player.play()
                self.state = 'playing'
                
                # Wait a bit for tracks to be available
                time.sleep(0.5)
                self._update_track_info()
                
                # Start monitoring thread
                if self.monitor_thread is None or not self.monitor_thread.is_alive():
                    self.monitor_stop_event.clear()
                    self.monitor_thread = Thread(target=self._monitor_playback)
                    self.monitor_thread.daemon = True
                    self.monitor_thread.start()
                
                logger.info(f"Playing: {video_path}")
                return True
            except Exception as e:
                logger.error(f"Error playing video: {e}")
                return False
        else:
            logger.info(f"Simulating playback of: {video_path}")
            self.state = 'playing'
            return True
    
    def pause(self):
        """Pause playback"""
        if self.video_available and self.player:
            self.player.pause()
        self.state = 'paused'
        logger.info("Paused")
    
    def resume(self):
        """Resume playback"""
        if self.video_available and self.player:
            self.player.play()
        self.state = 'playing'
        logger.info("Resumed")
    
    def stop(self):
        """Stop playback"""
        if self.video_available and self.player:
            self.player.stop()
        self.state = 'stopped'
        self.monitor_stop_event.set()
        logger.info("Stopped")
    
    def next(self):
        """Skip to next video"""
        if self.current_index < len(self.current_playlist) - 1:
            self.current_index += 1
            self.play(track_index=self.current_index)
        else:
            logger.info("Already at last video")
    
    def previous(self):
        """Go to previous video"""
        if self.current_index > 0:
            self.current_index -= 1
            self.play(track_index=self.current_index)
        else:
            logger.info("Already at first video")
    
    def set_volume(self, volume):
        """Set playback volume (0-100)"""
        self.volume = max(0, min(100, volume))
        if self.video_available and self.player:
            self.player.audio_set_volume(self.volume)
        logger.info(f"Volume set to {self.volume}")
    
    def set_audio_track(self, track_index):
        """Set audio track"""
        if self.video_available and self.player:
            try:
                self.player.audio_set_track(track_index)
                self.current_audio_track = track_index
                logger.info(f"Audio track set to {track_index}")
                return True
            except Exception as e:
                logger.error(f"Error setting audio track: {e}")
                return False
        return False
    
    def set_subtitle_track(self, track_index):
        """Set subtitle track (-1 to disable)"""
        if self.video_available and self.player:
            try:
                if track_index == -1:
                    self.player.video_set_spu(-1)
                else:
                    self.player.video_set_spu(track_index)
                self.current_subtitle_track = track_index
                logger.info(f"Subtitle track set to {track_index}")
                return True
            except Exception as e:
                logger.error(f"Error setting subtitle track: {e}")
                return False
        return False
    
    def _update_track_info(self):
        """Update available audio and subtitle tracks"""
        if not self.video_available or not self.player:
            return
        
        try:
            # Get audio tracks
            audio_tracks = self.player.audio_get_track_description()
            self.audio_tracks = []
            for track in audio_tracks:
                if track[0] >= 0:  # Valid track ID
                    self.audio_tracks.append({
                        'index': track[0],
                        'description': track[1].decode('utf-8') if isinstance(track[1], bytes) else str(track[1])
                    })
            
            # Get subtitle tracks
            subtitle_tracks = self.player.video_get_spu_description()
            self.subtitle_tracks = []
            for track in subtitle_tracks:
                if track[0] >= 0:  # Valid track ID
                    self.subtitle_tracks.append({
                        'index': track[0],
                        'description': track[1].decode('utf-8') if isinstance(track[1], bytes) else str(track[1])
                    })
            
            logger.info(f"Found {len(self.audio_tracks)} audio tracks, {len(self.subtitle_tracks)} subtitle tracks")
        except Exception as e:
            logger.error(f"Error updating track info: {e}")
    
    def _monitor_playback(self):
        """Monitor playback and handle end of video"""
        while not self.monitor_stop_event.is_set():
            time.sleep(1)
            
            if self.state == 'playing':
                if self.video_available and self.player:
                    state = self.player.get_state()
                    if state == vlc.State.Ended:
                        logger.info("Video ended, playing next")
                        self.next()
                    elif state == vlc.State.Error:
                        logger.error("Playback error")
                        self.stop()
    
    def get_status(self):
        """Get current playback status"""
        status = {
            'state': self.state,
            'current_index': self.current_index,
            'playlist_length': len(self.current_playlist),
            'volume': self.volume,
            'audio_tracks': self.audio_tracks,
            'subtitle_tracks': self.subtitle_tracks,
            'current_audio_track': self.current_audio_track,
            'current_subtitle_track': self.current_subtitle_track
        }
        
        if self.current_playlist and 0 <= self.current_index < len(self.current_playlist):
            status['current_track'] = self.current_playlist[self.current_index]
        
        if self.video_available and self.player and self.state == 'playing':
            try:
                status['position'] = self.player.get_position()
                status['time'] = self.player.get_time()
                status['length'] = self.player.get_length()
            except Exception as e:
                logger.warning(f"Error getting playback position: {e}")
        
        return status
    
    def get_playlist_tracks(self):
        """Get current playlist tracks"""
        return self.current_playlist
