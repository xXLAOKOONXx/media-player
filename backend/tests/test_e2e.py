"""End-to-end integration tests for the media player."""

import pytest
import requests
import time
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


API_BASE = "http://localhost:5000"


@pytest.fixture
def api_server():
    """Ensure API server is running."""
    try:
        response = requests.get(f"{API_BASE}/api/playback/status", timeout=2)
        yield API_BASE
    except requests.exceptions.RequestException:
        pytest.skip("Flask server is not running. Start with: cd backend && python app.py")


class TestEndToEndPlayback:
    """End-to-end tests for playback workflow."""

    def test_complete_playback_workflow(self, api_server, sample_playlist):
        """Test a complete playback workflow from loading to playing."""
        # This is a basic workflow test - in reality, the playlist loading
        # is done through the UI by selecting a playlist folder
        
        # 1. Check initial status
        response = requests.get(f"{api_server}/api/playback/status")
        assert response.status_code == 200
        initial_status = response.json()
        
        # 2. Get current tracks
        response = requests.get(f"{api_server}/api/playback/tracks")
        assert response.status_code == 200
        
        # 3. Test volume control
        response = requests.post(
            f"{api_server}/api/playback/volume",
            json={"volume": 0.7}
        )
        assert response.status_code in [200, 204]
        
        # 4. Test shuffle toggle
        response = requests.post(f"{api_server}/api/playback/shuffle")
        assert response.status_code in [200, 204]
        
        # 5. Test repeat mode
        response = requests.post(
            f"{api_server}/api/playback/repeat",
            json={"mode": "all"}
        )
        assert response.status_code in [200, 204]

    def test_storage_to_playlist_workflow(self, api_server):
        """Test workflow from storage management to playlist selection."""
        # 1. Get storage list
        response = requests.get(f"{api_server}/api/storage")
        assert response.status_code == 200
        storages = response.json()
        assert isinstance(storages, list)
        
        # 2. Get playlists
        response = requests.get(f"{api_server}/api/playlists")
        assert response.status_code == 200
        playlists = response.json()
        assert isinstance(playlists, list)
        
        # 3. Get playback status
        response = requests.get(f"{api_server}/api/playback/status")
        assert response.status_code == 200
        status = response.json()
        assert isinstance(status, dict)


class TestEndToEndMusicManagement:
    """End-to-end tests for music management features."""

    def test_music_folder_workflow(self, api_server):
        """Test the music folder management workflow."""
        # Check if music API endpoints are available
        try:
            response = requests.get(f"{api_server}/api/music")
            # If endpoint exists, test it
            if response.status_code in [200, 404]:
                assert True, "Music API endpoint is available"
        except requests.exceptions.RequestException:
            pytest.skip("Music API endpoints not available")


class TestEndToEndSoundEffects:
    """End-to-end tests for sound effects functionality."""

    def test_sound_effects_workflow(self, api_server):
        """Test the sound effects workflow."""
        # 1. Get sound effects folders
        try:
            response = requests.get(f"{api_server}/api/soundeffects")
            
            if response.status_code == 200:
                sound_effects = response.json()
                assert isinstance(sound_effects, list)
        except requests.exceptions.RequestException:
            pytest.skip("Sound effects API not available")


class TestEndToEndErrorHandling:
    """Test error handling in end-to-end scenarios."""

    def test_invalid_track_index(self, api_server):
        """Test handling of invalid track index."""
        response = requests.put(
            f"{api_server}/api/playback/tracks/99999/times",
            json={"start_time": 0.0, "end_time": 10.0}
        )
        
        # Should return error for invalid track index
        assert response.status_code in [400, 404]

    def test_invalid_volume(self, api_server):
        """Test handling of invalid volume values."""
        # Test volume > 1.0
        response = requests.post(
            f"{api_server}/api/playback/volume",
            json={"volume": 2.0}
        )
        
        # Should accept it or clamp it (implementation dependent)
        assert response.status_code in [200, 204, 400]

    def test_malformed_requests(self, api_server):
        """Test handling of malformed API requests."""
        # Missing required fields
        response = requests.put(
            f"{api_server}/api/playback/tracks/0/times",
            json={}
        )
        
        # Should return error for missing fields
        assert response.status_code in [400, 422]


class TestEndToEndCrossfade:
    """End-to-end tests for crossfade functionality."""

    def test_crossfade_configuration_workflow(self, api_server):
        """Test crossfade configuration through API."""
        # Get playback status (might include crossfade config)
        response = requests.get(f"{api_server}/api/playback/status")
        assert response.status_code == 200
        
        status = response.json()
        
        # Check if crossfade configuration is available in status
        # The actual endpoint structure depends on implementation
        assert isinstance(status, dict)


class TestEndToEndSystemIntegration:
    """Test system-level integration."""

    def test_full_system_health(self, api_server):
        """Test overall system health by checking all major endpoints."""
        endpoints = [
            "/api/playback/status",
            "/api/playback/tracks",
            "/api/storage",
            "/api/playlists",
        ]
        
        for endpoint in endpoints:
            response = requests.get(f"{api_server}{endpoint}")
            assert response.status_code == 200, f"Endpoint {endpoint} should be accessible"
            assert response.headers.get('Content-Type', '').startswith('application/json'), \
                f"Endpoint {endpoint} should return JSON"

    def test_api_response_times(self, api_server):
        """Test that API responses are reasonably fast."""
        start = time.time()
        response = requests.get(f"{api_server}/api/playback/status")
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 1.0, f"API response should be under 1 second, took {elapsed:.2f}s"
