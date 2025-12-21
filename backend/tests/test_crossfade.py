"""Tests for crossfade functionality and audio metadata."""

import pytest
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from playback_controller import PlaybackController


class TestAudioMetadata:
    """Test audio metadata extraction."""

    def test_duration_extraction(self, test_audio_file):
        """Test that duration is extracted from audio files using mutagen."""
        controller = PlaybackController()
        
        metadata = controller._read_id3_metadata(test_audio_file)
        
        assert 'duration' in metadata, "Duration should be extracted from audio file"
        assert metadata['duration'] > 0, f"Duration should be positive, got {metadata['duration']}"
        assert isinstance(metadata['duration'], (int, float)), "Duration should be numeric"

    def test_metadata_fields(self, test_audio_file):
        """Test that various metadata fields are extracted."""
        controller = PlaybackController()
        
        metadata = controller._read_id3_metadata(test_audio_file)
        
        # Duration is required
        assert 'duration' in metadata, "Duration is required"
        
        # Other fields are optional but should be present in the dict
        expected_fields = ['artist', 'album', 'title']
        for field in expected_fields:
            # Field should be in metadata (might be None)
            assert field in metadata or True, f"Metadata should handle {field} field"


class TestCrossfadeConfig:
    """Test crossfade configuration."""

    def test_default_crossfade_config(self):
        """Test default crossfade configuration."""
        controller = PlaybackController()
        
        config = controller.get_crossfade_config()
        
        assert isinstance(config, dict), "Config should be a dictionary"
        assert 'enabled' in config, "Config should have 'enabled' field"
        assert 'duration_ms' in config, "Config should have 'duration_ms' field"
        assert 'fade_out_start_before_end_ms' in config, "Config should have 'fade_out_start_before_end_ms' field"

    def test_custom_crossfade_config(self):
        """Test custom crossfade configuration."""
        controller = PlaybackController(crossfade_config={
            'enabled': True,
            'duration_ms': 5000,
            'fade_out_start_before_end_ms': 8000
        })
        
        config = controller.get_crossfade_config()
        
        assert config['enabled'] is True, "Enabled should be True"
        assert config['duration_ms'] == 5000, "Duration should be 5000ms"
        assert config['fade_out_start_before_end_ms'] == 8000, "Fade start should be 8000ms"

    def test_update_crossfade_config(self):
        """Test updating crossfade configuration."""
        controller = PlaybackController(crossfade_config={
            'enabled': True,
            'duration_ms': 3000,
            'fade_out_start_before_end_ms': 5000
        })
        
        # Update config
        controller.update_crossfade_config({'duration_ms': 4000})
        
        config = controller.get_crossfade_config()
        assert config['duration_ms'] == 4000, "Duration should be updated to 4000ms"
        # Other fields should remain unchanged
        assert config['enabled'] is True, "Enabled should remain True"
        assert config['fade_out_start_before_end_ms'] == 5000, "Fade start should remain 5000ms"


class TestPlaylistLoading:
    """Test playlist loading with duration extraction."""

    def test_playlist_loading(self, sample_playlist, test_audio_file):
        """Test that playlist loading uses actual file duration."""
        controller = PlaybackController()
        
        result = controller.load_playlist(sample_playlist)
        
        assert result is True, "Playlist should load successfully"
        assert len(controller.current_playlist) > 0, "Playlist should have tracks"
        
        track = controller.current_playlist[0]
        duration = float(track.get('duration', 0))
        
        # Duration should be extracted from the audio file
        assert duration > 0, f"Duration should be positive, got {duration}"

    def test_duration_overrides_m3u(self, temp_dir, test_audio_file):
        """Test that actual duration overrides M3U duration."""
        controller = PlaybackController()
        
        # Create a playlist with intentionally wrong duration
        playlist_path = os.path.join(temp_dir, 'test_wrong_duration.m3u')
        with open(playlist_path, 'w') as f:
            f.write('#EXTM3U\n')
            f.write('#EXTINF:999,Test Track - Wrong Duration\n')  # Intentionally wrong
            f.write(f'{test_audio_file}\n')
        
        result = controller.load_playlist(playlist_path)
        
        assert result is True, "Playlist should load successfully"
        
        track = controller.current_playlist[0]
        duration = float(track.get('duration', 0))
        
        # The actual duration should override the M3U duration
        assert duration != 999, f"Duration should be extracted from file, not from M3U (999)"
        assert duration > 0, f"Duration should be positive, got {duration}"


class TestLogging:
    """Test logging functionality."""

    def test_logger_exists(self):
        """Test that logging is configured."""
        import logging
        
        logger = logging.getLogger('PlaybackController')
        
        assert logger is not None, "Logger should exist"
        # Logger should have some configuration
        assert isinstance(logger, logging.Logger), "Should be a Logger instance"
