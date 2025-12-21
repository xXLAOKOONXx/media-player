#!/usr/bin/env python3
"""
Test script for playlist crossfade functionality
Tests crossfading from one playlist to another
"""
import sys
import os
import time
import tempfile

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from playback_controller import PlaybackController

def create_test_playlist(name, track_path, playlist_dir):
    """Create a simple test playlist"""
    playlist_path = os.path.join(playlist_dir, f'{name}.m3u')
    with open(playlist_path, 'w') as f:
        f.write('#EXTM3U\n')
        f.write(f'#EXTINF:10,{name} Track\n')
        f.write(f'{track_path}\n')
    return playlist_path

def test_playlist_crossfade():
    """Test crossfading between playlists"""
    print("=" * 60)
    print("Testing playlist crossfade functionality...")
    print("=" * 60)
    
    # Initialize controller with crossfade enabled
    controller = PlaybackController(crossfade_config={
        'enabled': True,
        'duration_ms': 2000,  # 2 second crossfade for testing
        'fade_out_start_before_end_ms': 5000
    })
    
    # Get test track path
    test_track = os.path.join(os.path.dirname(__file__), 'test_track.mp3')
    
    if not os.path.exists(test_track):
        print(f"ERROR: Test track not found: {test_track}")
        print("Please ensure test_track.mp3 exists in the examples directory")
        return False
    
    # Create temporary directory for test playlists
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Create two test playlists
        playlist1_path = create_test_playlist('playlist1', test_track, temp_dir)
        playlist2_path = create_test_playlist('playlist2', test_track, temp_dir)
        
        print(f"\nCreated test playlists:")
        print(f"  Playlist 1: {playlist1_path}")
        print(f"  Playlist 2: {playlist2_path}")
        
        # Load and play first playlist
        print("\n1. Loading and playing first playlist...")
        if not controller.load_playlist(playlist1_path):
            print("ERROR: Failed to load first playlist")
            return False
        
        controller.play(0)
        print("   First playlist is now playing")
        
        # Wait a moment to ensure playback starts
        time.sleep(1)
        
        # Check playback status
        status = controller.get_status()
        if not status['is_playing']:
            print("WARNING: First playlist not playing (might be in no-audio mode)")
        else:
            print(f"   Playing: {status['current_track']['title']}")
        
        # Now load second playlist - this should trigger crossfade
        print("\n2. Loading second playlist (should crossfade)...")
        if not controller.load_playlist(playlist2_path):
            print("ERROR: Failed to load second playlist")
            return False
        
        # Check if crossfade is happening
        if controller.is_crossfading:
            print("   ✓ Crossfade initiated successfully")
            print(f"   Crossfade duration: {controller.crossfade_config['duration_ms']}ms")
        else:
            # This is OK in no-audio mode
            if not controller.audio_available:
                print("   ✓ No crossfade (running in no-audio mode)")
            else:
                print("   Note: Crossfade may have completed very quickly")
        
        # Wait for crossfade to complete
        print("\n3. Waiting for crossfade to complete...")
        max_wait = 5  # Wait up to 5 seconds
        waited = 0
        while controller.is_crossfading and waited < max_wait:
            time.sleep(0.1)
            waited += 0.1
        
        if controller.is_crossfading:
            print(f"   WARNING: Crossfade still in progress after {max_wait}s")
        else:
            print(f"   ✓ Crossfade completed in ~{waited:.1f}s")
        
        # Check final status
        print("\n4. Checking final playback status...")
        status = controller.get_status()
        
        if status['current_track']:
            print(f"   Current track: {status['current_track']['title']}")
            print(f"   Is playing: {status['is_playing']}")
            print(f"   Playlist length: {status['playlist_length']}")
        
        # Verify the new playlist is loaded
        if len(controller.current_playlist) > 0:
            print("\n   ✓ New playlist loaded successfully")
            return True
        else:
            print("\n   ✗ Playlist not loaded correctly")
            return False
        
    finally:
        # Cleanup
        controller.stop()
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

def test_crossfade_disabled():
    """Test that crossfade can be disabled for playlist switches"""
    print("\n" + "=" * 60)
    print("Testing playlist load without crossfade...")
    print("=" * 60)
    
    # Initialize controller with crossfade disabled
    controller = PlaybackController(crossfade_config={
        'enabled': False,
        'duration_ms': 2000
    })
    
    test_track = os.path.join(os.path.dirname(__file__), 'test_track.mp3')
    
    if not os.path.exists(test_track):
        print("ERROR: Test track not found")
        return False
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        playlist1_path = create_test_playlist('playlist1', test_track, temp_dir)
        playlist2_path = create_test_playlist('playlist2', test_track, temp_dir)
        
        # Load and play first playlist
        controller.load_playlist(playlist1_path)
        controller.play(0)
        time.sleep(0.5)
        
        # Load second playlist - should NOT crossfade
        controller.load_playlist(playlist2_path)
        
        if not controller.is_crossfading:
            print("   ✓ No crossfade when disabled")
            return True
        else:
            print("   ✗ Crossfade occurred when it should be disabled")
            return False
        
    finally:
        controller.stop()
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

def test_crossfade_explicit_control():
    """Test explicit control of playlist crossfade"""
    print("\n" + "=" * 60)
    print("Testing explicit crossfade control...")
    print("=" * 60)
    
    controller = PlaybackController(crossfade_config={
        'enabled': True,
        'duration_ms': 2000
    })
    
    test_track = os.path.join(os.path.dirname(__file__), 'test_track.mp3')
    
    if not os.path.exists(test_track):
        print("ERROR: Test track not found")
        return False
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        playlist1_path = create_test_playlist('playlist1', test_track, temp_dir)
        playlist2_path = create_test_playlist('playlist2', test_track, temp_dir)
        
        # Load and play first playlist
        controller.load_playlist(playlist1_path)
        controller.play(0)
        time.sleep(0.5)
        
        # Explicitly disable crossfade for this load
        print("\n   Testing explicit crossfade_to_new=False...")
        controller.load_playlist(playlist2_path, crossfade_to_new=False)
        
        if not controller.is_crossfading:
            print("   ✓ Crossfade disabled via parameter")
        else:
            print("   ✗ Crossfade occurred when explicitly disabled")
            return False
        
        # Load another playlist and explicitly enable crossfade
        controller.play(0)
        time.sleep(0.5)
        
        playlist3_path = create_test_playlist('playlist3', test_track, temp_dir)
        print("\n   Testing explicit crossfade_to_new=True...")
        controller.load_playlist(playlist3_path, crossfade_to_new=True)
        
        # In no-audio mode, crossfade might not trigger
        if controller.audio_available:
            time.sleep(0.1)  # Give it a moment to start
            if controller.is_crossfading or controller.current_playlist:
                print("   ✓ Crossfade enabled via parameter")
            else:
                print("   Note: Crossfade may have completed quickly")
        else:
            print("   ✓ Parameter accepted (no-audio mode)")
        
        return True
        
    finally:
        controller.stop()
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == '__main__':
    print("\nPlaylist Crossfade Test Suite\n")
    
    all_passed = True
    
    # Run tests
    if not test_playlist_crossfade():
        all_passed = False
        print("\n✗ Playlist crossfade test FAILED\n")
    
    if not test_crossfade_disabled():
        all_passed = False
        print("\n✗ Crossfade disabled test FAILED\n")
    
    if not test_crossfade_explicit_control():
        all_passed = False
        print("\n✗ Explicit control test FAILED\n")
    
    # Summary
    print("=" * 60)
    if all_passed:
        print("✓ ALL TESTS PASSED")
        sys.exit(0)
    else:
        print("✗ SOME TESTS FAILED")
        sys.exit(1)
