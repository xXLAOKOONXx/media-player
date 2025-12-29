"""Tests for URL restructuring and routing."""

import pytest
import requests


API_BASE = "http://localhost:5000"


@pytest.fixture
def api_available():
    """Check if API server is running."""
    try:
        response = requests.get(f"{API_BASE}/api/audio/playback/status", timeout=2)
        if response.status_code != 200:
            pytest.skip(
                f"Flask server is not running (or wrong service/auth). Expected 200 from /api/audio/playback/status, got {response.status_code}"
            )
        return True
    except requests.exceptions.RequestException:
        pytest.skip("Flask server is not running. Start with: cd backend && python app.py")


class TestAudioAPIRoutes:
    """Test new audio API routes under /api/audio/."""

    def test_audio_playback_status(self, api_available):
        """Test the new audio playback status endpoint."""
        response = requests.get(f"{API_BASE}/api/audio/playback/status")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, dict), "Response should be a dictionary"

    def test_audio_playlists_endpoint(self, api_available):
        """Test the new audio playlists endpoint."""
        response = requests.get(f"{API_BASE}/api/audio/playlists")
        if response.status_code in (401, 403):
            pytest.skip("Audio playlists endpoint requires authentication")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"

    def test_audio_storage_endpoint(self, api_available):
        """Test the new audio storage endpoint."""
        response = requests.get(f"{API_BASE}/api/audio/storage")
        if response.status_code in (401, 403):
            pytest.skip("Audio storage endpoint requires authentication")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"

    def test_audio_music_endpoint(self, api_available):
        """Test the new audio music endpoint."""
        response = requests.get(f"{API_BASE}/api/audio/music")
        if response.status_code in (401, 403):
            pytest.skip("Audio music endpoint requires authentication")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"

    def test_audio_soundeffects_endpoint(self, api_available):
        """Test the new audio soundeffects endpoint."""
        response = requests.get(f"{API_BASE}/api/audio/soundeffects")
        if response.status_code in (401, 403):
            pytest.skip("Audio soundeffects endpoint requires authentication")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"

    def test_audio_tracks_endpoint(self, api_available):
        """Test the new audio tracks endpoint."""
        response = requests.get(f"{API_BASE}/api/audio/playback/tracks")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "tracks" in data, "Response should contain tracks list"
        assert isinstance(data["tracks"], list), "Tracks should be a list"


class TestFrontendRoutes:
    """Test frontend URL routes."""

    def test_root_redirects(self, api_available):
        """Test that root path redirects or serves the app."""
        response = requests.get(f"{API_BASE}/", allow_redirects=False)
        # Should either redirect or serve index.html (200)
        assert response.status_code in [200, 301, 302, 303, 307, 308], \
            f"Expected redirect or 200, got {response.status_code}"

    def test_old_api_routes_return_404(self, api_available):
        """Test that old /api/* routes (without /audio/) return 404."""
        # Test a few old routes to ensure they're removed
        old_routes = [
            f"{API_BASE}/api/playback/status",
            f"{API_BASE}/api/playlists",
            f"{API_BASE}/api/storage"
        ]
        
        for route in old_routes:
            response = requests.get(route)
            assert response.status_code == 404, f"Old route {route} should return 404, got {response.status_code}"

    def test_audio_player_route(self, api_available):
        """Test that /audio/player route serves the app."""
        response = requests.get(f"{API_BASE}/audio/player")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        # Should serve HTML
        assert 'text/html' in response.headers.get('Content-Type', ''), \
            "Should serve HTML content"

    def test_audio_playlists_route(self, api_available):
        """Test that /audio/playlists route serves the app."""
        response = requests.get(f"{API_BASE}/audio/playlists")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    def test_audio_music_route(self, api_available):
        """Test that /audio/music route serves the app."""
        response = requests.get(f"{API_BASE}/audio/music")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    def test_audio_soundeffects_route(self, api_available):
        """Test that /audio/soundeffects route serves the app."""
        response = requests.get(f"{API_BASE}/audio/soundeffects")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    def test_audio_storage_route(self, api_available):
        """Test that /audio/storage route serves the app."""
        response = requests.get(f"{API_BASE}/audio/storage")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    def test_audio_tracks_route(self, api_available):
        """Test that /audio/tracks route serves the app."""
        response = requests.get(f"{API_BASE}/audio/tracks")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    def test_video_route(self, api_available):
        """Test that /video route serves the app."""
        response = requests.get(f"{API_BASE}/video")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        # Should serve HTML
        assert 'text/html' in response.headers.get('Content-Type', ''), \
            "Should serve HTML content"
