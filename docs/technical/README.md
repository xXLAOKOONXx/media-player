# Technical Documentation

This directory contains detailed technical documentation about the Media Player's architecture, APIs, and implementation.

## Core Documentation

### System Architecture

- **[Architecture](architecture.md)** - System overview and design
  - Component diagram
  - Data flow
  - Technology stack
  - Integration points

### Backend

- **[API Documentation](api.md)** - REST API reference
  - All endpoints
  - Request/response formats
  - Error handling
  - Examples

- **[Security](security.md)** - Security considerations
  - Current security status
  - Known issues
  - Recommendations
  - Best practices for production

### Frontend

- **[Frontend](frontend.md)** - Vite frontend build system
  - Why Vite over Create React App
  - Build process
  - Integration with Flask
  - Development workflow

### Quality Assurance

- **[Testing](testing.md)** - Testing infrastructure and guide
  - Test structure
  - Running tests
  - Writing new tests
  - CI/CD integration

- **[Bundling](bundling.md)** - Creating distributable bundles
  - Windows executable bundles
  - Unix distribution packages
  - Platform-specific considerations

## Features

### Audio Features

- **[Crossfading](crossfading.md)** - Crossfade implementation details
  - Automatic duration detection
  - True overlapping crossfade
  - Smart memory management
  - Performance monitoring
  - Configuration options

- **[Custom Track Times](custom-track-times.md)** - Custom start/end times
  - Feature description
  - Implementation components
  - API endpoints
  - Database schema
  - Frontend integration

### Library Management

- **[Music Tab Usage](music-tab-usage.md)** - Music library management
  - Configuring playlist folders
  - Adding music folders
  - Searching and filtering
  - Creating playlists
  - Metadata management

## Technology Stack

### Backend
- **Python 3.8+** - Core language
- **Flask** - Web framework
- **SQLite** - Database
- **pygame** - Audio playback
- **mutagen** - Audio metadata extraction

### Frontend
- **React** - UI framework
- **TypeScript** - Type-safe JavaScript
- **Vite** - Build tool
- **Tailwind CSS** - Styling

### Infrastructure
- **systemd** - Service management (Linux)
- **ALSA/HDMI** - Audio output
- **SMB/NFS** - Network storage

## Architecture Overview

```
┌─────────────────┐
│  React Frontend │ (Vite + TypeScript)
└────────┬────────┘
         │ HTTP/REST
┌────────▼────────┐
│   Flask Backend │ (Python + Flask)
├─────────────────┤
│ - Storage Mgr   │
│ - Library Mgr   │
│ - Playback Ctrl │
└────────┬────────┘
         │
┌────────▼────────┐
│  pygame.mixer   │ (Audio Engine)
└────────┬────────┘
         │
┌────────▼────────┐
│   ALSA/HDMI     │ (Audio Output)
└─────────────────┘
```

## Development Workflow

### Setting Up Development Environment
1. Follow [Quick Start Guide](../installation/quickstart.md)
2. Review [Architecture](architecture.md) to understand the system
3. Check [Frontend](frontend.md) for frontend development details

### Making Changes
1. Write tests (see [Testing](testing.md))
2. Implement changes
3. Run tests locally
4. Update documentation as needed
5. Create pull request

### Adding New Features
1. Review [Architecture](architecture.md) for integration points
2. Update [API Documentation](api.md) if adding new endpoints
3. Follow [UI Guidance](../ui-guidance/README.md) for frontend changes
4. Add tests (see [Testing](testing.md))
5. Update relevant requirements in [Requirements](../requirements/README.md)

## API Quick Reference

### Audio Playback
- `GET /api/audio/playback/status` - Get current playback status
- `POST /api/audio/playback/play` - Start playback
- `POST /api/audio/playback/pause` - Pause playback
- `POST /api/audio/playback/stop` - Stop playback
- `POST /api/audio/playback/next` - Skip to next track
- `POST /api/audio/playback/previous` - Go to previous track

### Storage Management
- `GET /api/audio/storage` - List all network storages
- `POST /api/audio/storage` - Add new storage
- `DELETE /api/audio/storage/{id}` - Remove storage

### Library Management
- `GET /api/audio/library` - List all libraries
- `POST /api/audio/library` - Add new library
- `GET /api/audio/library/{id}` - Get library details

For complete API documentation, see [API Documentation](api.md).

## Key Implementation Details

### Audio Playback
- Uses pygame.mixer for audio output
- Supports M3U playlists
- HDMI audio output for Raspberry Pi
- Crossfading with true overlap (see [Crossfading](crossfading.md))

### Database
- SQLite for configuration and cache
- Platform-specific storage locations
- Automatic migrations

### Network Storage
- SMB/CIFS support
- NFS support
- Automatic mounting
- Credential management

## Performance Considerations

### Backend
- Efficient audio streaming with pygame
- Minimal CPU usage during playback
- Smart caching for metadata

### Frontend
- Optimized Vite builds
- Code splitting for faster loads
- Efficient polling intervals

### Raspberry Pi
- HDMI audio configuration
- Memory management for crossfading
- Service priority tuning

See [Raspberry Pi Setup](../installation/raspberry-pi.md#performance-tuning) for optimization details.

## Security

⚠️ **Important**: This application is designed for private home networks.

See [Security](security.md) for:
- Current security status
- Known issues
- Recommendations for production use
- Hardening checklist

## Related Documentation

- [Installation Guides](../installation/README.md) - Setup and deployment
- [Requirements](../requirements/README.md) - UI behavior specifications
- [UI Guidance](../ui-guidance/README.md) - UI design guidelines
- [Contributing](../../CONTRIBUTING.md) - Contribution guidelines
