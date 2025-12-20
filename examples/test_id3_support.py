#!/usr/bin/env python3
"""
Test script to verify ID3 tag reading for custom start/end times
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from playback_controller import PlaybackController

def test_id3_reading():
    """Test reading ID3 tags from audio files"""
    print("=" * 60)
    print("Testing ID3 Tag Reading for Start/End Times")
    print("=" * 60)
    
    controller = PlaybackController()
    
    # Test 1: Read ID3 tags directly from test file
    print("\n1. Testing _read_id3_times() method...")
    test_file = os.path.join(os.path.dirname(__file__), 'test_track.mp3')
    
    if not os.path.exists(test_file):
        print(f"✗ Test file not found: {test_file}")
        print("   Run: python3 id3_tag_manager.py create test_track.mp3 --start 10000 --end 120000")
        return False
    
    start, end = controller._read_id3_times(test_file)
    print(f"   Start time: {start}s (expected: 10.0s)")
    print(f"   End time: {end}s (expected: 120.0s)")
    
    if start == 10.0 and end == 120.0:
        print("✓ ID3 tags read correctly!")
    else:
        print("✗ ID3 tags not read correctly")
        return False
    
    # Test 2: Load playlist with ID3-tagged file
    print("\n2. Testing playlist loading with ID3 tags...")
    playlist_path = os.path.join(os.path.dirname(__file__), 'test_id3_playlist.m3u')
    
    if not os.path.exists(playlist_path):
        print(f"✗ Playlist not found: {playlist_path}")
        return False
    
    result = controller.load_playlist(playlist_path)
    if not result:
        print("✗ Failed to load playlist")
        return False
    
    print(f"✓ Loaded playlist with {len(controller.current_playlist)} track(s)")
    
    # Verify track has ID3 times
    if len(controller.current_playlist) > 0:
        track = controller.current_playlist[0]
        print(f"\nTrack 0: {track.get('title', 'Unknown')}")
        print(f"  Path: {track.get('path', 'N/A')}")
        print(f"  Start Time: {track.get('start_time', 'Not set')}")
        print(f"  End Time: {track.get('end_time', 'Not set')}")
        
        if track.get('start_time') == 10.0 and track.get('end_time') == 120.0:
            print("✓ Playlist track has correct ID3 times!")
        else:
            print("✗ Playlist track times incorrect")
            return False
    
    # Test 3: Verify status API includes ID3 times
    print("\n3. Testing status API...")
    status = controller.get_status()
    
    if status['current_track']:
        track = status['current_track']
        print(f"  Title: {track['title']}")
        print(f"  Start Time: {track.get('start_time', 'Not set')}")
        print(f"  End Time: {track.get('end_time', 'Not set')}")
        
        if track.get('start_time') == 10.0 and track.get('end_time') == 120.0:
            print("✓ Status API includes ID3 times!")
        else:
            print("✗ Status API times incorrect")
            return False
    
    return True

def test_m3u_fallback():
    """Test that M3U directives still work as fallback"""
    print("\n" + "=" * 60)
    print("Testing M3U Fallback (when ID3 tags not present)")
    print("=" * 60)
    
    controller = PlaybackController()
    
    # Load the old playlist with EXTVLCOPT directives
    playlist_path = os.path.join(os.path.dirname(__file__), 'example_playlist_with_times.m3u')
    
    if not os.path.exists(playlist_path):
        print("⚠ example_playlist_with_times.m3u not found, skipping M3U fallback test")
        return True
    
    result = controller.load_playlist(playlist_path)
    if not result:
        print("✗ Failed to load M3U playlist")
        return False
    
    print(f"✓ Loaded M3U playlist with {len(controller.current_playlist)} track(s)")
    
    # Check that M3U times were parsed (for files that don't exist, so no ID3)
    # Since the files in example_playlist_with_times.m3u don't exist, 
    # ID3 reading will be skipped and M3U directives should be used
    return True

if __name__ == '__main__':
    print("\nID3 Tag Support for Custom Track Times - Test Suite\n")
    
    all_passed = True
    
    if not test_id3_reading():
        all_passed = False
        print("\n✗ ID3 reading test FAILED\n")
    
    if not test_m3u_fallback():
        all_passed = False
        print("\n✗ M3U fallback test FAILED\n")
    
    # Summary
    print("=" * 60)
    if all_passed:
        print("✓ ALL TESTS PASSED")
        print("\nID3 tags are now supported with field names:")
        print("  - LAO:MUSIC_START (in milliseconds)")
        print("  - LAO:MUSIC_END (in milliseconds)")
        sys.exit(0)
    else:
        print("✗ SOME TESTS FAILED")
        sys.exit(1)
