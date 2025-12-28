"""
Tests for stats tracking functionality
"""

import os
import pytest
import tempfile
import shutil
import sqlite3
from stats_manager import StatsManager


class TestStatsManager:
    """Test the StatsManager class"""
    
    @pytest.fixture
    def temp_stats_folder(self):
        """Create a temporary folder for stats database"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_stats_manager_initialization(self, temp_stats_folder):
        """Test that StatsManager initializes correctly"""
        manager = StatsManager(temp_stats_folder)
        
        assert manager.is_initialized()
        assert manager.stats_folder == temp_stats_folder
        assert manager.db_path == os.path.join(temp_stats_folder, 'media-player-stats.db')
        assert os.path.exists(manager.db_path)
    
    def test_stats_manager_no_folder(self):
        """Test that StatsManager handles no folder correctly"""
        manager = StatsManager(None)
        
        assert not manager.is_initialized()
        assert manager.db_path is None
    
    def test_record_media_stat(self, temp_stats_folder):
        """Test recording a media stat"""
        manager = StatsManager(temp_stats_folder)
        
        # Record a stat
        success = manager.record_media_stat('/path/to/media/file.mp4', 'testuser')
        assert success
        
        # Verify it was recorded
        stats = manager.get_media_stats()
        assert len(stats) == 1
        assert stats[0]['file_path'] == '/path/to/media/file.mp4'
        assert stats[0]['username'] == 'testuser'
        assert 'timestamp' in stats[0]
        assert 'id' in stats[0]
    
    def test_record_multiple_stats(self, temp_stats_folder):
        """Test recording multiple stats"""
        manager = StatsManager(temp_stats_folder)
        
        # Record multiple stats
        manager.record_media_stat('/path/to/file1.mp3', 'user1')
        manager.record_media_stat('/path/to/file2.mp3', 'user2')
        manager.record_media_stat('/path/to/file3.mp3', 'user1')
        
        # Verify all were recorded
        stats = manager.get_media_stats()
        assert len(stats) == 3
    
    def test_get_media_stats_by_username(self, temp_stats_folder):
        """Test filtering stats by username"""
        manager = StatsManager(temp_stats_folder)
        
        # Record stats for different users
        manager.record_media_stat('/path/to/file1.mp3', 'user1')
        manager.record_media_stat('/path/to/file2.mp3', 'user2')
        manager.record_media_stat('/path/to/file3.mp3', 'user1')
        
        # Filter by user1
        user1_stats = manager.get_media_stats(username='user1')
        assert len(user1_stats) == 2
        for stat in user1_stats:
            assert stat['username'] == 'user1'
        
        # Filter by user2
        user2_stats = manager.get_media_stats(username='user2')
        assert len(user2_stats) == 1
        assert user2_stats[0]['username'] == 'user2'
    
    def test_get_media_stats_with_limit(self, temp_stats_folder):
        """Test limiting the number of returned stats"""
        manager = StatsManager(temp_stats_folder)
        
        # Record multiple stats
        for i in range(10):
            manager.record_media_stat(f'/path/to/file{i}.mp3', 'testuser')
        
        # Get limited stats
        stats = manager.get_media_stats(limit=5)
        assert len(stats) == 5
    
    def test_record_stat_without_initialization(self):
        """Test that recording without initialization fails gracefully"""
        manager = StatsManager(None)
        
        success = manager.record_media_stat('/path/to/file.mp3', 'testuser')
        assert not success
    
    def test_set_stats_folder(self, temp_stats_folder):
        """Test changing the stats folder"""
        manager = StatsManager(None)
        assert not manager.is_initialized()
        
        # Set the folder
        manager.set_stats_folder(temp_stats_folder)
        assert manager.is_initialized()
        assert manager.stats_folder == temp_stats_folder
        
        # Verify database was created
        assert os.path.exists(manager.db_path)
        
        # Test recording works
        success = manager.record_media_stat('/test/file.mp3', 'testuser')
        assert success

    def test_legacy_db_with_folder_path_column_is_supported(self, temp_stats_folder):
        """Existing DBs may have a legacy schema with folder_path.

        The manager should still initialize and allow recording (we now pass file paths).
        """
        db_path = os.path.join(temp_stats_folder, 'media-player-stats.db')

        conn = sqlite3.connect(db_path, timeout=5.0)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS media_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                folder_path TEXT NOT NULL,
                username TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

        manager = StatsManager(temp_stats_folder)
        assert manager.is_initialized()

        # Should write a file path into the legacy column without failing
        success = manager.record_media_stat('/path/to/media/file.mp4', 'testuser')
        assert success

        stats = manager.get_media_stats(limit=1)
        assert stats and stats[0]['file_path'] == '/path/to/media/file.mp4'


class TestStatsTracking:
    """Test stats tracking in playback controllers"""
    
    def test_stats_threshold_calculation(self):
        """Test the threshold calculation (50% or 5 minutes)"""
        # For a 10 minute (600s) track: 50% = 300s, min(300, 300) = 300s
        duration1 = 600.0
        threshold1 = min(duration1 * 0.5, 300.0)
        assert threshold1 == 300.0
        
        # For a 4 minute (240s) track: 50% = 120s, min(120, 300) = 120s
        duration2 = 240.0
        threshold2 = min(duration2 * 0.5, 300.0)
        assert threshold2 == 120.0
        
        # For a 15 minute (900s) track: 50% = 450s, min(450, 300) = 300s
        duration3 = 900.0
        threshold3 = min(duration3 * 0.5, 300.0)
        assert threshold3 == 300.0
