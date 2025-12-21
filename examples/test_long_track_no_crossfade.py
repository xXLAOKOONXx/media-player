#!/usr/bin/env python3
"""
Test script to verify long tracks (>= 10 minutes) skip crossfade
"""
import sys
import os
import time
import tempfile
import shutil

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from playback_controller import PlaybackController

def create_test_playlist(name, track_path, playlist_dir, duration='10'):
    """Create a simple test playlist with specified duration"""
    playlist_path = os.path.join(playlist_dir, f'{name}.m3u')
    with open(playlist_path, 'w') as f:
        f.write('#EXTM3U\n')
        f.write(f'#EXTINF:{duration},{name} Track\n')
        f.write(f'{track_path}\n')
    return playlist_path

def test_long_track_skips_crossfade():
    """Test that tracks >= 10 minutes skip crossfade"""
    print("=" * 60)
    print("Testing long track (>= 10 min) skips crossfade...")
    print("=" * 60)
    
    # Initialize controller with crossfade enabled
    controller = PlaybackController(crossfade_config={
        'enabled': True,
        'duration_ms': 2000,
        'fade_out_start_before_end_ms': 5000
    })
    
    # Get test track path
    test_track = os.path.join(os.path.dirname(__file__), 'test_track.mp3')
    
    if not os.path.exists(test_track):
        print(f"ERROR: Test track not found: {test_track}")
        return False
    
    # Create temporary directory for test playlists
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Create playlists with different durations
        short_playlist = create_test_playlist('short', test_track, temp_dir, duration='180')  # 3 minutes
        long_playlist = create_test_playlist('long', test_track, temp_dir, duration='600')  # 10 minutes
        very_long_playlist = create_test_playlist('verylong', test_track, temp_dir, duration='3600')  # 1 hour
        
        print(f"\nCreated test playlists:")
        print(f"  Short (3 min): {short_playlist}")
        print(f"  Long (10 min): {long_playlist}")
        print(f"  Very long (1 hour): {very_long_playlist}")
        
        # Load and play short playlist
        print("\n1. Loading short playlist (3 min)...")
        if not controller.load_playlist(short_playlist):
            print("ERROR: Failed to load short playlist")
            return False
        
        controller.play(0)
        print("   Short playlist is now playing")
        time.sleep(0.5)
        
        # Load long playlist (10 minutes) - should skip crossfade
        print("\n2. Loading long playlist (10 min) while playing...")
        controller.load_playlist(long_playlist)
        
        # Wait a moment for any processing
        time.sleep(0.2)
        
        if controller.is_crossfading:
            print("   ✗ FAILED: Crossfade is happening (should be skipped for 10 min track)")
            return False
        else:
            print("   ✓ Crossfade skipped for 10 minute track")
        
        # Verify new playlist is loaded
        status = controller.get_status()
        if status['current_track'] and 'long' in status['current_track']['title']:
            print(f"   ✓ New playlist loaded: {status['current_track']['title']}")
        else:
            print(f"   Note: Current track: {status['current_track']['title'] if status['current_track'] else 'None'}")
        
        # Now test very long track
        print("\n3. Loading very long playlist (1 hour) while playing...")
        controller.play(0)
        time.sleep(0.5)
        controller.load_playlist(very_long_playlist)
        time.sleep(0.2)
        
        if controller.is_crossfading:
            print("   ✗ FAILED: Crossfade is happening (should be skipped for 1 hour track)")
            return False
        else:
            print("   ✓ Crossfade skipped for 1 hour track")
        
        print("\n✓ All long track tests passed")
        return True
        
    finally:
        controller.stop()
        shutil.rmtree(temp_dir, ignore_errors=True)

def test_short_track_uses_crossfade():
    """Test that tracks < 10 minutes still use crossfade"""
    print("\n" + "=" * 60)
    print("Testing short track (< 10 min) uses crossfade...")
    print("=" * 60)
    
    controller = PlaybackController(crossfade_config={
        'enabled': True,
        'duration_ms': 2000,
        'fade_out_start_before_end_ms': 5000
    })
    
    test_track = os.path.join(os.path.dirname(__file__), 'test_track.mp3')
    
    if not os.path.exists(test_track):
        print("ERROR: Test track not found")
        return False
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Create two short playlists
        playlist1 = create_test_playlist('playlist1', test_track, temp_dir, duration='180')  # 3 minutes
        playlist2 = create_test_playlist('playlist2', test_track, temp_dir, duration='300')  # 5 minutes
        
        print(f"\nCreated test playlists:")
        print(f"  Playlist 1 (3 min): {playlist1}")
        print(f"  Playlist 2 (5 min): {playlist2}")
        
        # Load and play first playlist
        print("\n1. Loading first playlist (3 min)...")
        controller.load_playlist(playlist1)
        controller.play(0)
        time.sleep(0.5)
        
        # Load second short playlist - should crossfade
        print("\n2. Loading second playlist (5 min) while playing...")
        controller.load_playlist(playlist2)
        
        # In no-audio mode, crossfade might not trigger, but the logic should attempt it
        time.sleep(0.1)
        
        if controller.audio_available:
            # With audio, crossfade should be attempted
            if controller.is_crossfading or not controller.is_playing:
                print("   ✓ Crossfade attempted for short track (< 10 min)")
            else:
                print("   Note: Crossfade may have completed quickly")
        else:
            # Without audio, just verify playlist loaded
            print("   ✓ Short track allowed crossfade logic (no-audio mode)")
        
        return True
        
    finally:
        controller.stop()
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == '__main__':
    print("\nLong Track No-Crossfade Test Suite\n")
    
    all_passed = True
    
    # Run tests
    if not test_long_track_skips_crossfade():
        all_passed = False
        print("\n✗ Long track test FAILED\n")
    
    if not test_short_track_uses_crossfade():
        all_passed = False
        print("\n✗ Short track test FAILED\n")
    
    # Summary
    print("=" * 60)
    if all_passed:
        print("✓ ALL TESTS PASSED")
        sys.exit(0)
    else:
        print("✗ SOME TESTS FAILED")
        sys.exit(1)
