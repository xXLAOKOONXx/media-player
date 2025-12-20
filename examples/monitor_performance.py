#!/usr/bin/env python3
"""
Example: Monitoring crossfade performance with logging

This example demonstrates how to use the logging mechanism to monitor
crossfade performance in real-world scenarios.
"""
import sys
import os
import logging

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from playback_controller import PlaybackController

# Configure logging to file for analysis
log_file = '/tmp/media_player_performance.log'
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()  # Also print to console
    ]
)

logger = logging.getLogger('PerformanceMonitor')

def monitor_playback():
    """Example of monitoring crossfade performance"""
    
    logger.info("=" * 60)
    logger.info("Starting Performance Monitoring Example")
    logger.info("=" * 60)
    
    # Create controller with custom crossfade settings
    controller = PlaybackController(crossfade_config={
        'enabled': True,
        'duration_ms': 2000,  # 2 second crossfade for demo
        'fade_out_start_before_end_ms': 3000  # Start 3 seconds before end
    })
    
    logger.info("Created PlaybackController with 2s crossfade")
    
    # Load a test playlist
    test_playlist_path = '/tmp/performance_test.m3u'
    test_track = os.path.join(os.path.dirname(__file__), 'test_track.mp3')
    
    # Create a playlist with multiple copies of the test track
    with open(test_playlist_path, 'w') as f:
        f.write('#EXTM3U\n')
        for i in range(3):
            f.write(f'#EXTINF:999,Test Track {i+1}\n')
            f.write(f'{test_track}\n')
    
    logger.info(f"Created test playlist with 3 tracks")
    
    result = controller.load_playlist(test_playlist_path)
    if result:
        logger.info(f"Playlist loaded successfully")
        logger.info(f"Tracks: {len(controller.current_playlist)}")
        
        # Show track durations
        for i, track in enumerate(controller.current_playlist):
            duration = track.get('duration', 'unknown')
            logger.info(f"  Track {i+1}: {track['title']} - Duration: {duration}s")
    else:
        logger.error("Failed to load playlist")
        return
    
    logger.info("")
    logger.info("Performance monitoring is now active!")
    logger.info(f"All logs are being written to: {log_file}")
    logger.info("")
    logger.info("In a real scenario, you would:")
    logger.info("  1. Start playback: controller.play()")
    logger.info("  2. Let tracks play and crossfade automatically")
    logger.info("  3. Review logs to analyze performance")
    logger.info("")
    logger.info("Log entries will show:")
    logger.info("  - When crossfade starts")
    logger.info("  - Volume levels during crossfade")
    logger.info("  - When crossfade completes")
    logger.info("  - Any errors or fallback mechanisms")
    logger.info("")
    logger.info("Example log output during crossfade:")
    logger.info("  INFO - Starting crossfade: 2000ms overlap between tracks")
    logger.info("  DEBUG - Crossfade 0%: current=0.50, next=0.00")
    logger.info("  DEBUG - Crossfade 20%: current=0.40, next=0.10")
    logger.info("  DEBUG - Crossfade 40%: current=0.30, next=0.20")
    logger.info("  DEBUG - Crossfade 60%: current=0.20, next=0.30")
    logger.info("  DEBUG - Crossfade 80%: current=0.10, next=0.40")
    logger.info("  DEBUG - Crossfade 100%: current=0.00, next=0.50")
    logger.info("  INFO - Crossfade complete - now playing: Test Track 2")
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("Performance Monitoring Example Complete")
    logger.info("=" * 60)

if __name__ == '__main__':
    monitor_playback()
    
    print("\n" + "=" * 60)
    print(f"✓ Log file created: {log_file}")
    print(f"  You can analyze it with:")
    print(f"    cat {log_file}")
    print(f"    grep 'Crossfade' {log_file}")
    print(f"    grep 'ERROR' {log_file}")
    print("=" * 60)
