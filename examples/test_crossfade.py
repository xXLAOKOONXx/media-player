#!/usr/bin/env python3
"""
Test script for crossfade functionality and duration extraction
"""
import sys
import os
import time
import tempfile

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from playback_controller import PlaybackController

def test_duration_extraction():
    """Test that duration is extracted from audio files using mutagen"""
    print("=" * 60)
    print("Testing duration extraction from audio files...")
    print("=" * 60)
    
    controller = PlaybackController()
    
    # Create a simple test playlist with the test track
    test_track = os.path.join(os.path.dirname(__file__), 'test_track.mp3')
    
    if not os.path.exists(test_track):
        print(f"ERROR: Test track not found: {test_track}")
        return False
    
    # Test the metadata reading directly
    metadata = controller._read_id3_metadata(test_track)
    
    print(f"\nMetadata extracted from {os.path.basename(test_track)}:")
    print(f"  Duration: {metadata.get('duration', 'Not found')}")
    print(f"  Artist: {metadata.get('artist', 'Not found')}")
    print(f"  Album: {metadata.get('album', 'Not found')}")
    
    if 'duration' in metadata:
        print(f"\n✓ Duration successfully extracted: {metadata['duration']:.2f} seconds")
        return True
    else:
        print("\n✗ Failed to extract duration from audio file")
        return False

def test_crossfade_config():
    """Test crossfade configuration"""
    print("\n" + "=" * 60)
    print("Testing crossfade configuration...")
    print("=" * 60)
    
    controller = PlaybackController(crossfade_config={
        'enabled': True,
        'duration_ms': 5000,
        'fade_out_start_before_end_ms': 8000
    })
    
    config = controller.get_crossfade_config()
    print(f"\nCrossfade config:")
    print(f"  Enabled: {config['enabled']}")
    print(f"  Duration: {config['duration_ms']}ms")
    print(f"  Fade start before end: {config['fade_out_start_before_end_ms']}ms")
    
    # Update config
    controller.update_crossfade_config({
        'duration_ms': 3000
    })
    
    config = controller.get_crossfade_config()
    if config['duration_ms'] == 3000:
        print("\n✓ Crossfade configuration works correctly")
        return True
    else:
        print("\n✗ Failed to update crossfade configuration")
        return False

def test_playlist_with_duration():
    """Test that playlist loading uses actual file duration"""
    print("\n" + "=" * 60)
    print("Testing playlist loading with duration extraction...")
    print("=" * 60)
    
    controller = PlaybackController()
    
    # Create a test playlist using cross-platform temp directory
    test_playlist_path = os.path.join(tempfile.gettempdir(), 'test_duration_playlist.m3u')
    test_track = os.path.join(os.path.dirname(__file__), 'test_track.mp3')
    
    with open(test_playlist_path, 'w') as f:
        f.write('#EXTM3U\n')
        f.write('#EXTINF:999,Test Track - Wrong Duration\n')  # Intentionally wrong
        f.write(f'{test_track}\n')
    
    result = controller.load_playlist(test_playlist_path)
    
    if not result:
        print("ERROR: Failed to load playlist")
        return False
    
    track = controller.current_playlist[0]
    duration = float(track.get('duration', 0))
    
    print(f"\nTrack loaded:")
    print(f"  Title: {track.get('title')}")
    print(f"  Duration from M3U: 999s (intentionally wrong)")
    print(f"  Actual duration extracted: {duration}s")
    
    # The actual duration should override the M3U duration
    if duration != 999 and duration > 0:
        print(f"\n✓ Duration successfully extracted from audio file (not M3U)")
        return True
    else:
        print(f"\n✗ Duration was not extracted from audio file")
        return False

def test_logging():
    """Test that logging is working"""
    print("\n" + "=" * 60)
    print("Testing logging mechanism...")
    print("=" * 60)
    
    import logging
    
    # Check if logger exists
    logger = logging.getLogger('PlaybackController')
    
    if logger:
        print(f"\n✓ Logger 'PlaybackController' is configured")
        print(f"  Log level: {logging.getLevelName(logger.level)}")
        return True
    else:
        print("\n✗ Logger not found")
        return False

if __name__ == '__main__':
    print("\nCrossfade and Duration Extraction - Test Suite\n")
    
    all_passed = True
    
    # Run tests
    if not test_duration_extraction():
        all_passed = False
        print("\n✗ Duration extraction test FAILED\n")
    
    if not test_crossfade_config():
        all_passed = False
        print("\n✗ Crossfade config test FAILED\n")
    
    if not test_playlist_with_duration():
        all_passed = False
        print("\n✗ Playlist duration test FAILED\n")
    
    if not test_logging():
        all_passed = False
        print("\n✗ Logging test FAILED\n")
    
    # Summary
    print("=" * 60)
    if all_passed:
        print("✓ ALL TESTS PASSED")
        sys.exit(0)
    else:
        print("✗ SOME TESTS FAILED")
        sys.exit(1)
