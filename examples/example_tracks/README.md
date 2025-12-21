# Example Test Audio Files

This directory contains test audio files used by the testing suite.

## Files

- `test_track.mp3` - A sample MP3 audio file with ID3v2.4 metadata (5.2KB, ~3 seconds)
  - Format: MPEG ADTS, layer III, v1
  - Bitrate: 128 kbps
  - Sample rate: 44.1 kHz
  - Channels: Stereo

## Usage

These files are used by the automated tests in the `backend/tests/` directory to test:
- Audio playback functionality
- Metadata extraction
- Crossfade features
- Playlist management
- Duration detection

## Adding More Test Files

To add more test audio files for testing:
1. Place the audio file in this directory
2. Update this README with file details
3. Update the test fixtures in `backend/tests/conftest.py` if needed

## Test assets

These files are intentionally kept small for automated testing:

- They are MP3 (low bitrate) and clipped to ~20 seconds.
- They include ID3 metadata (artist/title/album/track).

Files:

- 838029__lightfoot402__classical-guitar-riff.mp3
	- Artist: Lightfoot402
	- Title: Classical Guitar Riff
	- Album: Media Player Example Tracks
	- Track: 1
- 838972__boatlanman__sunny-days-100bpm.mp3
	- Artist: Boatlanman-
	- Title: Sunny Days (100 BPM)
	- Album: Media Player Example Tracks
	- Track: 2
- 838975__bassimat__ambient-low-frequency-drum-loop-soundscape-texture-002-at-120bpm.mp3
	- Artist: bassimat
	- Title: Ambient Low Frequency Drum Loop (120 BPM)
	- Album: Media Player Example Tracks
	- Track: 3
