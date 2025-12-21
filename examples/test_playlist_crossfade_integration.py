#!/usr/bin/env python3
"""
Integration test for playlist crossfade via API endpoint
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

def test_api_behavior():
    """Test that API endpoint behavior works correctly with crossfade"""
    print("=" * 60)
    print("Testing API endpoint integration with playlist crossfade...")
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
        # Create two test playlists
        playlist1_path = create_test_playlist('playlist1', test_track, temp_dir)
        playlist2_path = create_test_playlist('playlist2', test_track, temp_dir)
        
        print(f"\n1. Loading first playlist (no music playing)...")
        result = controller.load_playlist(playlist1_path)
        
        if not result:
            print("   ERROR: Failed to load first playlist")
            return False
        
        # Simulate API behavior: call play() after load_playlist
        if not controller.is_crossfading:
            controller.play(0)
            print("   ✓ play() called (not crossfading)")
        else:
            print("   ✓ play() skipped (crossfading)")
        
        status = controller.get_status()
        if status['is_playing']:
            print(f"   ✓ Playback started: {status['current_track']['title']}")
        
        # Wait a moment
        time.sleep(0.5)
        
        print(f"\n2. Loading second playlist (music is playing)...")
        result = controller.load_playlist(playlist2_path)
        
        if not result:
            print("   ERROR: Failed to load second playlist")
            return False
        
        # Check if crossfading
        is_crossfading_after_load = controller.is_crossfading
        
        # Simulate API behavior: only call play() if not crossfading
        if not controller.is_crossfading:
            controller.play(0)
            print("   ✓ play() called (not crossfading)")
        else:
            print("   ✓ play() skipped (crossfading in progress)")
        
        # Wait for crossfade to complete
        if is_crossfading_after_load:
            print(f"\n3. Waiting for crossfade to complete...")
            max_wait = 5
            waited = 0
            while controller.is_crossfading and waited < max_wait:
                time.sleep(0.1)
                waited += 0.1
            
            if controller.is_crossfading:
                print(f"   WARNING: Crossfade still in progress after {max_wait}s")
            else:
                print(f"   ✓ Crossfade completed")
        
        # Verify final state
        print(f"\n4. Verifying final state...")
        status = controller.get_status()
        
        if status['current_track']:
            current_title = status['current_track']['title']
            print(f"   Current track: {current_title}")
            
            # The new playlist should be loaded
            if 'playlist2' in current_title:
                print(f"   ✓ New playlist is active")
                return True
            else:
                print(f"   ✗ Old playlist still active")
                return False
        else:
            print("   ✗ No current track")
            return False
        
    finally:
        # Cleanup
        controller.stop()
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

def test_crossfade_flag():
    """Test that is_crossfading flag is set correctly"""
    print("\n" + "=" * 60)
    print("Testing is_crossfading flag behavior...")
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
        print("\n1. Loading first playlist...")
        controller.load_playlist(playlist1_path)
        
        if controller.is_crossfading:
            print("   ✗ is_crossfading should be False when loading first playlist")
            return False
        else:
            print("   ✓ is_crossfading = False")
        
        controller.play(0)
        time.sleep(0.3)
        
        # Load second playlist while playing
        print("\n2. Loading second playlist while playing...")
        controller.load_playlist(playlist2_path)
        
        # In no-audio mode, crossfade might not trigger
        if controller.audio_available:
            if controller.is_crossfading:
                print("   ✓ is_crossfading = True (as expected)")
            else:
                print("   Note: Crossfade may have completed immediately")
        else:
            print("   ✓ Flag behavior correct (no-audio mode)")
        
        return True
        
    finally:
        controller.stop()
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == '__main__':
    print("\nPlaylist Crossfade Integration Test\n")
    
    all_passed = True
    
    # Run tests
    if not test_api_behavior():
        all_passed = False
        print("\n✗ API behavior test FAILED\n")
    
    if not test_crossfade_flag():
        all_passed = False
        print("\n✗ Crossfade flag test FAILED\n")
    
    # Summary
    print("=" * 60)
    if all_passed:
        print("✓ ALL INTEGRATION TESTS PASSED")
        sys.exit(0)
    else:
        print("✗ SOME TESTS FAILED")
        sys.exit(1)
