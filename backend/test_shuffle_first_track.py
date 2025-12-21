#!/usr/bin/env python3
"""
Test script to verify that the first track is random when shuffle is enabled
before loading a playlist.
"""

import sys
import os
import tempfile
import shutil
import traceback
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from playback_controller import PlaybackController

def create_test_playlist(num_tracks=10):
    """Create a simple test playlist with numbered tracks"""
    # Create a temporary directory for test files
    temp_dir = tempfile.mkdtemp()
    playlist_path = os.path.join(temp_dir, "test_playlist.m3u")
    
    # Create the playlist file
    with open(playlist_path, 'w') as f:
        f.write("#EXTM3U\n")
        for i in range(num_tracks):
            f.write(f"#EXTINF:180,Track {i+1}\n")
            # Create empty track files
            track_file = os.path.join(temp_dir, f"track{i+1}.mp3")
            Path(track_file).touch()
            f.write(f"{track_file}\n")
    
    return playlist_path, temp_dir

def test_shuffle_first_track():
    """Test that first track is random when shuffle is enabled before loading playlist"""
    print("Testing random first track with shuffle enabled...")
    
    # Create test playlist
    playlist_path, temp_dir = create_test_playlist(10)
    print(f"Created test playlist: {playlist_path}")
    
    # Test 1: Load playlist WITHOUT shuffle - should always start at track 0
    print("\n=== Test 1: Loading playlist WITHOUT shuffle ===")
    controller = PlaybackController()
    controller.load_playlist(playlist_path)
    first_track = controller.current_playlist[0]['title']
    print(f"First track (no shuffle): {first_track}")
    assert first_track == "Track 1", "Without shuffle, first track should be Track 1"
    print("✓ Test 1 passed: First track is Track 1 (as expected)")
    
    # Test 2: Enable shuffle THEN load playlist - first track should be random
    print("\n=== Test 2: Enable shuffle BEFORE loading playlist ===")
    first_tracks = []
    for i in range(20):  # Load multiple times to check randomness
        controller = PlaybackController()
        controller.set_shuffle(True)
        controller.load_playlist(playlist_path)
        first_track = controller.current_playlist[0]['title']
        first_tracks.append(first_track)
    
    print(f"First tracks across 20 loads: {first_tracks}")
    unique_first_tracks = set(first_tracks)
    print(f"Unique first tracks: {unique_first_tracks}")
    print(f"Number of unique first tracks: {len(unique_first_tracks)}")
    
    # With 10 tracks and 20 iterations, we should see at least 3 different first tracks
    # (statistically very unlikely to see only 1 or 2 if truly random)
    assert len(unique_first_tracks) >= 3, f"Expected at least 3 different first tracks, got {len(unique_first_tracks)}"
    print(f"✓ Test 2 passed: Got {len(unique_first_tracks)} different first tracks (random selection works)")
    
    # Test 3: Load playlist, start playing, THEN enable shuffle - current track should stay
    print("\n=== Test 3: Enable shuffle AFTER loading playlist ===")
    controller = PlaybackController()
    controller.load_playlist(playlist_path)
    original_first_track = controller.current_playlist[0]['title']
    print(f"Original first track: {original_first_track}")
    
    # Simulate moving to a different track
    controller.current_track_index = 5
    current_track_before_shuffle = controller.current_playlist[5]['title']
    print(f"Currently at track index 5: {current_track_before_shuffle}")
    
    # Enable shuffle while playing
    controller.set_shuffle(True)
    first_track_after_shuffle = controller.current_playlist[0]['title']
    print(f"First track after enabling shuffle: {first_track_after_shuffle}")
    
    # The track that was playing (at index 5) should now be at index 0
    assert first_track_after_shuffle == current_track_before_shuffle, \
        "Current track should be preserved when enabling shuffle during playback"
    print("✓ Test 3 passed: Current track preserved when enabling shuffle during playback")
    
    # Cleanup
    shutil.rmtree(temp_dir)
    
    print("\n" + "="*60)
    print("✓ ALL TESTS PASSED!")
    print("="*60)
    return True

if __name__ == '__main__':
    try:
        success = test_shuffle_first_track()
        sys.exit(0 if success else 1)
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        traceback.print_exc()
        sys.exit(1)
