"""Tests for Flask API endpoints."""

import pytest
import requests
import time


API_BASE = "http://localhost:5000"


@pytest.fixture
def api_available():
    """Check if API server is running."""
    try:
        response = requests.get(f"{API_BASE}/api/playback/status", timeout=2)
        return True
    except requests.exceptions.RequestException:
        pytest.skip("Flask server is not running. Start with: cd backend && python app.py")


class TestPlaybackAPI:
    """Test playback API endpoints."""

    def test_status_endpoint(self, api_available):
        """Test the status endpoint."""
        response = requests.get(f"{API_BASE}/api/playback/status")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, dict), "Response should be a dictionary"
        # Status endpoint should return playback state information
        assert "state" in data or "status" in data, "Response should contain state/status"

    def test_tracks_endpoint(self, api_available):
        """Test the tracks endpoint."""
        response = requests.get(f"{API_BASE}/api/playback/tracks")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "tracks" in data, "Response should contain tracks list"
        assert isinstance(data["tracks"], list), "Tracks should be a list"

    def test_volume_endpoint(self, api_available):
        """Test setting volume."""
        # Get current volume
        response = requests.get(f"{API_BASE}/api/playback/status")
        assert response.status_code == 200
        
        # Set volume to 50%
        response = requests.post(
            f"{API_BASE}/api/playback/volume",
            json={"volume": 0.5}
        )
        # Volume endpoint might return 200 or 204
        assert response.status_code in [200, 204], f"Expected 200 or 204, got {response.status_code}"


class TestTrackTimes:
    """Test custom track times functionality."""

    def test_set_track_times(self, api_available):
        """Test setting track times."""
        # First, check if we have any tracks loaded
        response = requests.get(f"{API_BASE}/api/playback/tracks")
        tracks = response.json().get('tracks', [])
        
        if len(tracks) == 0:
            pytest.skip("No playlist loaded, cannot test track times")
        
        # Set custom times for first track
        response = requests.put(
            f"{API_BASE}/api/playback/tracks/0/times",
            json={
                "start_time": 15.0,
                "end_time": 90.0
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Verify the change
        response = requests.get(f"{API_BASE}/api/playback/tracks")
        tracks = response.json().get('tracks', [])
        
        if len(tracks) > 0:
            track = tracks[0]
            assert track.get('start_time') == 15.0, f"Start time should be 15.0, got {track.get('start_time')}"
            assert track.get('end_time') == 90.0, f"End time should be 90.0, got {track.get('end_time')}"

    def test_validation_negative_start_time(self, api_available):
        """Test that negative start time is rejected."""
        response = requests.put(
            f"{API_BASE}/api/playback/tracks/0/times",
            json={"start_time": -10.0}
        )
        
        assert response.status_code == 400, f"Should reject negative start time, got {response.status_code}"

    def test_validation_start_after_end(self, api_available):
        """Test that start_time >= end_time is rejected."""
        response = requests.put(
            f"{API_BASE}/api/playback/tracks/0/times",
            json={"start_time": 100.0, "end_time": 50.0}
        )
        
        assert response.status_code == 400, f"Should reject start >= end, got {response.status_code}"


class TestStorageAPI:
    """Test storage management API endpoints."""

    def test_get_storage(self, api_available):
        """Test getting storage list."""
        response = requests.get(f"{API_BASE}/api/storage")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Storage list should be a list"


class TestPlaylistAPI:
    """Test playlist management API endpoints."""

    def test_get_playlists(self, api_available):
        """Test getting playlists."""
        response = requests.get(f"{API_BASE}/api/playlists")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Playlists should be a list"
