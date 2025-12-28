# Crossfade Implementation

## Overview

This document describes the crossfade implementation in the media player, which provides smooth transitions between tracks with real audio overlap.

## Key Features

### 1. Automatic Duration Detection

The media player uses **mutagen** library to extract accurate track duration directly from audio files:

- Supports multiple audio formats (MP3, FLAC, OGG, M4A, etc.)
- Duration is extracted from file metadata, not M3U playlist files
- Falls back to M3U duration if file reading fails

**Implementation:**
```python
def _read_id3_metadata(self, file_path):
    audio = MutagenFile(file_path)
    if hasattr(audio.info, 'length'):
        metadata['duration'] = audio.info.length
```

### 2. True Overlapping Crossfade

Unlike simple queue-based crossfade (where next track starts after current finishes), this implementation provides **simultaneous playback** of both tracks during the crossfade period.

**How It Works:**

1. **Normal Playback**: Tracks play using `pygame.mixer.music` for efficient streaming
2. **Crossfade Detection**: Monitor thread detects when track approaches end (configurable threshold)
3. **Overlap Playback**: 
   - Next track is loaded as `pygame.mixer.Sound` object
   - Both current track (music) and next track (sound channel) play simultaneously
   - Volume gradually fades: current decreases, next increases
4. **Seamless Transition**: After crossfade completes, next track continues via music player

**Configuration:**
```python
crossfade_config = {
    'enabled': True,
    'duration_ms': 3000,  # 3 seconds crossfade
    'fade_out_start_before_end_ms': 5000  # Start 5 seconds before end
}
```

### 3. Smart Memory Management

**Challenge**: Loading entire audio files into memory can cause issues with large files.

**Solution**: Hybrid approach with automatic fallback:

1. **Primary Method** (for typical files): Load next track as Sound for true overlap
2. **Fallback Method** (for large files): Use queue-based crossfade if loading fails

```python
try:
    next_sound = pygame.mixer.Sound(next_track_path)
    # Perform simultaneous fade
except pygame.error:
    # Fallback to queue-based method
    pygame.mixer.music.queue(next_track_path)
```

### 4. Performance Monitoring

Comprehensive logging tracks all aspects of crossfade performance:

```python
logger.info(f"Starting crossfade: {duration_ms}ms overlap")
logger.debug(f"Crossfade {progress*100:.0f}%: current={vol1:.2f}, next={vol2:.2f}")
logger.info(f"Crossfade complete - now playing: {track_title}")
```

**Log Levels:**
- `INFO`: Track changes, crossfade start/completion
- `DEBUG`: Detailed fade progress, volume changes
- `WARNING`: File not found, memory issues
- `ERROR`: Exceptions, critical failures

## Technical Details

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   PlaybackController                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Normal Playback:                                        │
│  ┌───────────────────────────────────────────────┐     │
│  │ pygame.mixer.music (streaming)                 │     │
│  │ - Efficient for large files                    │     │
│  │ - Low memory usage                             │     │
│  └───────────────────────────────────────────────┘     │
│                                                          │
│  Crossfade Period:                                       │
│  ┌───────────────────────────────────────────────┐     │
│  │ pygame.mixer.music (fading out)                │     │
│  │         +                                       │     │
│  │ pygame.mixer.Sound on channel (fading in)      │     │
│  │ - Simultaneous playback                        │     │
│  │ - Gradual volume transition                    │     │
│  └───────────────────────────────────────────────┘     │
│                                                          │
│  ┌───────────────────────────────────────────────┐     │
│  │ Monitor Thread                                  │     │
│  │ - Tracks playback position                     │     │
│  │ - Triggers crossfade at right time             │     │
│  │ - Handles custom start/end times               │     │
│  └───────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────┘
```

### Crossfade Algorithm

1. **Detection Phase** (continuous monitoring):
   ```python
   current_position = (time.now() - track_start) + custom_start
   if current_position >= (track_end - fade_start_threshold):
       trigger_crossfade()
   ```

2. **Overlap Phase** (3 seconds default):
   ```python
   for step in range(100):
       progress = elapsed / duration
       current_volume = base_volume * (1.0 - progress)
       next_volume = base_volume * progress
       time.sleep(step_duration)
   ```

3. **Transition Phase**:
   ```python
   mixer.music.stop()  # Stop old track
   channel.stop()      # Stop Sound object
   mixer.music.load(next_track)  # Continue with music player
   mixer.music.play(start=already_played_duration)
   ```

### Pygame Mixer Setup

```python
pygame.mixer.init(
    frequency=44100,      # CD-quality audio
    size=-16,             # 16-bit signed
    channels=2,           # Stereo
    buffer=2048           # Balance latency vs. stability
)
pygame.mixer.set_num_channels(8)  # Allow multiple simultaneous sounds
```

## Testing

### Test Suite

Run the comprehensive test suite:
```bash
python examples/test_crossfade.py
```

Tests include:
1. Duration extraction from audio files
2. Crossfade configuration management
3. Playlist loading with duration override
4. Logging mechanism verification

### Manual Testing

To test crossfade manually:

1. Create a playlist with short tracks
2. Configure short crossfade for testing:
   ```python
   controller.update_crossfade_config({
       'duration_ms': 1000,  # 1 second
       'fade_out_start_before_end_ms': 2000  # Start 2 sec before end
   })
   ```
3. Play playlist and observe smooth transitions

## Performance Considerations

### Memory Usage

- **Normal playback**: Low (streaming)
- **During crossfade**: Medium (one track in memory)
- **Fallback mode**: Low (queue-based)

### CPU Usage

- **Volume fade calculations**: ~100 steps per crossfade = minimal CPU
- **Monitoring thread**: Checks every 0.1s = negligible overhead
- **Mutagen file reading**: One-time per track load

### Latency

- **Crossfade trigger**: < 100ms (monitoring interval)
- **Track transition**: Seamless (no gap)
- **Volume steps**: 30ms each (imperceptible)

## Troubleshooting

### Issue: Crossfade not triggering

**Check:**
1. Is crossfade enabled? `crossfade_config['enabled'] == True`
2. Is track duration detected? Check logs for duration extraction
3. Is fade_start threshold > track duration? Reduce threshold

### Issue: Gaps between tracks

**Possible causes:**
1. Large file fallback mode (expected minor gap)
2. System under heavy load (increase buffer size)
3. Network storage latency (pre-load next track earlier)

### Issue: High memory usage

**Solution:**
1. Check if many large files triggering Sound loading
2. Monitor logs for "Cannot load track as Sound" warnings
3. System automatically falls back to queue method

## Future Enhancements

Potential improvements:

1. **Adaptive crossfade**: Adjust duration based on track tempo/energy
2. **EQ during fade**: Frequency-dependent crossfade
3. **Pre-loading**: Load next track in background before crossfade
4. **Gapless playback**: Zero-gap option for live albums
5. **Fade curves**: Non-linear fade profiles (exponential, logarithmic)

## References

- [Pygame Documentation](https://www.pygame.org/docs/)
- [Mutagen Documentation](https://mutagen.readthedocs.io/)
- [Audio Crossfading Techniques](https://en.wikipedia.org/wiki/Fade_(audio_engineering))
