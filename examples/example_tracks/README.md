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
