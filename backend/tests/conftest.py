"""Pytest configuration and fixtures for media player tests."""

import os
import sys
import tempfile
import pytest
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture
def test_audio_file():
    """Provide path to the test audio file."""
    base_dir = Path(__file__).parent.parent.parent
    test_file = base_dir / "examples" / "example_tracks" / "test_track.mp3"
    if not test_file.exists():
        pytest.skip(f"Test audio file not found: {test_file}")
    return str(test_file)


@pytest.fixture
def temp_dir():
    """Provide a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_playlist(temp_dir, test_audio_file):
    """Create a sample M3U playlist for testing."""
    playlist_path = os.path.join(temp_dir, "test_playlist.m3u")
    with open(playlist_path, 'w') as f:
        f.write('#EXTM3U\n')
        f.write(f'#EXTINF:180,Test Artist - Test Track\n')
        f.write(f'{test_audio_file}\n')
    return playlist_path


@pytest.fixture
def sample_config(temp_dir):
    """Create a sample configuration for testing."""
    config = {
        "network_storages": [],
        "libraries": [],
        "crossfade": {
            "enabled": True,
            "duration_ms": 3000,
            "fade_out_start_before_end_ms": 5000
        }
    }
    return config


@pytest.fixture
def mock_storage_path(temp_dir):
    """Create a mock storage directory structure."""
    music_dir = Path(temp_dir) / "music"
    music_dir.mkdir()
    playlists_dir = Path(temp_dir) / "playlists"
    playlists_dir.mkdir()
    return {
        "music": str(music_dir),
        "playlists": str(playlists_dir),
        "root": temp_dir
    }
