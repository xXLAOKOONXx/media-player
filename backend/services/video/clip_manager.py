"""
Video Clip Manager
Handles creation and management of video clips using ffmpeg
"""

import os
import subprocess
import hashlib
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class ClipManager:
    """Manages video clip creation and storage"""
    
    def __init__(self, database_manager, default_clips_folder: Optional[str] = None):
        """
        Initialize ClipManager
        
        Args:
            database_manager: DatabaseManager instance for storing clip metadata
            default_clips_folder: Default folder for storing clips
        """
        self.db = database_manager
        self.default_clips_folder = default_clips_folder or self._get_default_clips_folder()
        
        # Ensure clips folder exists
        os.makedirs(self.default_clips_folder, exist_ok=True)
    
    def _get_default_clips_folder(self) -> str:
        """Get default clips folder from database or create default"""
        clips_folder = self.db.get_config('clips_folder')
        if not clips_folder:
            # Default to app data dir / clips
            from services.general.database_manager import get_app_data_dir
            clips_folder = os.path.join(get_app_data_dir(), 'clips')
            self.db.set_config('clips_folder', clips_folder)
        return clips_folder
    
    def get_clips_folder(self) -> str:
        """Get current clips folder path"""
        return self.default_clips_folder
    
    def set_clips_folder(self, folder_path: str) -> bool:
        """
        Set clips folder path
        
        Args:
            folder_path: New folder path for clips
            
        Returns:
            True if successful, False otherwise
        """
        try:
            os.makedirs(folder_path, exist_ok=True)
            self.default_clips_folder = folder_path
            self.db.set_config('clips_folder', folder_path)
            return True
        except Exception as e:
            logger.error(f"Failed to set clips folder: {e}")
            return False
    
    def _check_ffmpeg_available(self) -> bool:
        """Check if ffmpeg is available in the system"""
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def create_clip(
        self,
        source_video_path: str,
        start_position: float,
        duration: float = 60.0,
        source_media_id: Optional[str] = None,
        source_series_name: Optional[str] = None,
        user_id: Optional[int] = None,
        audio_track_index: Optional[int] = None,
        subtitle_track_index: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a video clip using ffmpeg
        
        Args:
            source_video_path: Path to source video file
            start_position: Start position in seconds (will create clip from start_position - 60 to start_position)
            duration: Duration of clip in seconds (default: 60)
            source_media_id: Media ID of source video
            source_series_name: Series name if source is part of a series
            user_id: ID of user creating the clip
            audio_track_index: Audio track ID to use (0-indexed, None for default)
            subtitle_track_index: Subtitle track ID to use (0-indexed, None for none)
            
        Returns:
            Dictionary with clip metadata or None if failed
        """
        if not self._check_ffmpeg_available():
            logger.error("ffmpeg is not available")
            return None
        
        if not os.path.exists(source_video_path):
            logger.error(f"Source video not found: {source_video_path}")
            return None
        
        # Calculate actual start time (60 seconds before current position)
        clip_start = max(0, start_position - duration)
        
        # Generate unique clip filename
        timestamp = int(time.time())
        source_basename = os.path.splitext(os.path.basename(source_video_path))[0]
        clip_filename = f"clip_{source_basename}_{timestamp}.mp4"
        clip_path = os.path.join(self.default_clips_folder, clip_filename)
        
        # Generate media_id for the clip
        clip_media_id = hashlib.sha256(clip_path.encode('utf-8')).hexdigest()
        
        try:
            # Build ffmpeg command
            cmd = [
                'ffmpeg',
                '-ss', str(clip_start),  # Start time
                '-i', source_video_path,  # Input file
                '-t', str(duration),  # Duration
                '-c:v', 'libx264',  # Video codec
                '-preset', 'medium',  # Encoding speed/quality tradeoff
                '-crf', '23',  # Quality (lower is better, 23 is default)
                '-c:a', 'aac',  # Audio codec
                '-b:a', '128k',  # Audio bitrate
            ]
            cmd.extend(['-map', '0:v:0'])  # Video track
            
            # Add audio track selection if specified
            if audio_track_index is not None and audio_track_index is not False:
                cmd.extend(['-map', f'0:a:{audio_track_index}'])  # Specific audio track
            
            # Add subtitle track selection if specified (burn into video)
            if subtitle_track_index is not None and subtitle_track_index is not False:
                # Note: Burning subtitles requires more complex filter
                # For now, we'll copy subtitle stream if available
                cmd.extend(['-map', f'0:s:{subtitle_track_index}?'])  # Optional subtitle
            
            # Add metadata
            metadata = []
            if source_media_id:
                metadata.extend(['-metadata', f'comment=Source: {source_media_id}'])
            if source_series_name:
                metadata.extend(['-metadata', f'show={source_series_name}'])
            metadata.extend(['-metadata', f'creation_time={time.strftime("%Y-%m-%d %H:%M:%S")}'])
            cmd.extend(metadata)
            
            # Output file
            cmd.extend(['-y', clip_path])  # -y to overwrite
            
            logger.info(f"Creating clip with command: {' '.join(cmd)}")
            
            # Execute ffmpeg
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=300,  # 5 minute timeout
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"ffmpeg failed: {result.stderr}")
                return None
            
            # Generate thumbnail from clip
            self._generate_thumbnail(clip_path)
            
            # Get clip duration
            clip_duration = self._get_video_duration(clip_path)
            
            # Store clip metadata in database
            conn = self.db._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO video_clips (
                    clip_media_id, source_media_id, source_file_path,
                    source_series_name, clip_file_path, clip_file_name,
                    clip_duration, source_position, created_at,
                    user_id, audio_track_index, subtitle_track_index
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                clip_media_id, source_media_id, source_video_path,
                source_series_name, clip_path, clip_filename,
                clip_duration, start_position, time.time(),
                user_id, audio_track_index, subtitle_track_index
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Clip created successfully: {clip_path}")
            
            return {
                'clip_media_id': clip_media_id,
                'clip_file_path': clip_path,
                'clip_file_name': clip_filename,
                'clip_duration': clip_duration,
                'source_position': start_position,
                'created_at': time.time()
            }
            
        except subprocess.TimeoutExpired:
            logger.error("ffmpeg timed out")
            return None
        except Exception as e:
            logger.error(f"Failed to create clip: {e}")
            return None
    
    def _generate_thumbnail(self, video_path: str) -> bool:
        """Generate thumbnail and embed it in the MP4 file"""
        try:
            # Generate thumbnail at 1 second into the clip
            thumb_path = video_path.replace('.mp4', '_thumb.jpg')
            
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-ss', '1',  # 1 second in
                '-vframes', '1',  # Single frame
                '-vf', 'scale=320:-1',  # Scale width to 320px, maintain aspect ratio
                '-y', thumb_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, timeout=30)
            
            if result.returncode == 0 and os.path.exists(thumb_path):
                # Embed thumbnail in MP4
                temp_output = video_path + '.temp.mp4'
                embed_cmd = [
                    'ffmpeg',
                    '-i', video_path,
                    '-i', thumb_path,
                    '-map', '0',  # Copy all streams from first input
                    '-map', '1',  # Add thumbnail from second input
                    '-c', 'copy',  # Copy streams without re-encoding
                    '-disposition:v:1', 'attached_pic',  # Mark as attached picture
                    '-y', temp_output
                ]
                
                embed_result = subprocess.run(embed_cmd, capture_output=True, timeout=60)
                
                if embed_result.returncode == 0:
                    # Replace original with thumbnail-embedded version
                    os.replace(temp_output, video_path)
                    os.remove(thumb_path)
                    return True
                else:
                    # Clean up temp file if it exists
                    if os.path.exists(temp_output):
                        os.remove(temp_output)
                
                # Clean up thumbnail file
                if os.path.exists(thumb_path):
                    os.remove(thumb_path)
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to generate thumbnail: {e}")
            return False
    
    def _get_video_duration(self, video_path: str) -> Optional[float]:
        """Get video duration using ffprobe"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, timeout=10, text=True)
            
            if result.returncode == 0:
                return float(result.stdout.strip())
            
        except Exception as e:
            logger.error(f"Failed to get video duration: {e}")
        
        return None
    
    def list_clips(self, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        List all clips, optionally filtered by user
        
        Args:
            user_id: Optional user ID to filter clips
            
        Returns:
            List of clip metadata dictionaries
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()
        
        if user_id is not None:
            cursor.execute('''
                SELECT * FROM video_clips
                WHERE user_id = ?
                ORDER BY created_at DESC
            ''', (user_id,))
        else:
            cursor.execute('''
                SELECT * FROM video_clips
                ORDER BY created_at DESC
            ''')
        
        columns = [desc[0] for desc in cursor.description]
        clips = []
        
        for row in cursor.fetchall():
            clip = dict(zip(columns, row))
            clips.append(clip)
        
        conn.close()
        return clips
    
    def get_clip(self, clip_media_id: str) -> Optional[Dict[str, Any]]:
        """
        Get clip metadata by media ID
        
        Args:
            clip_media_id: Clip media ID
            
        Returns:
            Clip metadata dictionary or None if not found
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM video_clips WHERE clip_media_id = ?', (clip_media_id,))
        row = cursor.fetchone()
        
        conn.close()
        
        if row:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
        
        return None
    
    def delete_clip(self, clip_media_id: str) -> bool:
        """
        Delete a clip by media ID
        
        Args:
            clip_media_id: Clip media ID
            
        Returns:
            True if successful, False otherwise
        """
        clip = self.get_clip(clip_media_id)
        if not clip:
            return False
        
        try:
            # Delete file
            if os.path.exists(clip['clip_file_path']):
                os.remove(clip['clip_file_path'])
            
            # Delete from database
            conn = self.db._get_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM video_clips WHERE clip_media_id = ?', (clip_media_id,))
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete clip: {e}")
            return False
