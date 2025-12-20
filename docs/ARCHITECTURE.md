# Architecture Documentation

## System Overview

The Media Player is a distributed application consisting of three main components:

1. **React Frontend**: Web-based user interface
2. **Flask Backend**: REST API and business logic
3. **Audio Subsystem**: Pygame-based audio playback

```mermaid
flowchart TB
    subgraph "Client Device"
        UI[React Web UI]
    end
    
    subgraph "Raspberry Pi"
        subgraph "Backend Services"
            API[Flask API]
            Storage[Storage Manager]
            Library[Library Manager]
            Playback[Playback Controller]
        end
        
        subgraph "Audio System"
            Pygame[Pygame Mixer]
            ALSA[ALSA Audio Driver]
        end
    end
    
    subgraph "Network Storage"
        NAS[NAS/File Server]
        SMB[SMB Share]
        NFS[NFS Share]
    end
    
    subgraph "Output"
        HDMI[HDMI Audio]
        Receiver[AV Receiver]
        Speakers[Speakers]
    end
    
    UI -->|HTTP REST| API
    API --> Storage
    API --> Library
    API --> Playback
    Storage -->|Mount| SMB
    Storage -->|Mount| NFS
    SMB --> NAS
    NFS --> NAS
    Library -->|Read| SMB
    Playback -->|Decode| Pygame
    Pygame --> ALSA
    ALSA --> HDMI
    HDMI --> Receiver
    Receiver --> Speakers
    
    style UI fill:#667eea
    style API fill:#764ba2
    style Pygame fill:#4facfe
    style Receiver fill:#43e97b
```

## Component Details

### Frontend (React + TypeScript)

#### Component Hierarchy

```mermaid
graph TD
    App[App.tsx]
    App --> Storage[StorageManager]
    App --> Library[LibraryManager]
    App --> Player[Player View]
    Player --> NowPlaying[NowPlaying]
    Player --> Controls[PlaybackControls]
    
    style App fill:#667eea
    style Storage fill:#764ba2
    style Library fill:#f093fb
    style NowPlaying fill:#4facfe
    style Controls fill:#43e97b
```

#### Key Features

1. **Tab Navigation**: Switch between Storage, Library, and Player views
2. **Real-time Updates**: Polls playback status every second
3. **Responsive Design**: Works on desktop and mobile devices
4. **Form Management**: Dynamic forms for adding storage and libraries

#### State Management

Currently uses React hooks (`useState`, `useEffect`) for state management. For larger applications, consider Redux or Zustand.

### Backend (Python + Flask)

#### Module Structure

```mermaid
graph LR
    subgraph "Flask Application"
        Main[app.py]
    end
    
    subgraph "Business Logic"
        SM[storage_manager.py]
        LM[library_manager.py]
        PC[playback_controller.py]
    end
    
    subgraph "Data Layer"
        Config[config.json]
        FS[File System]
        Audio[Audio Files]
    end
    
    Main --> SM
    Main --> LM
    Main --> PC
    SM --> Config
    LM --> FS
    PC --> Audio
    
    style Main fill:#667eea
    style SM fill:#764ba2
    style LM fill:#f093fb
    style PC fill:#4facfe
```

#### Storage Manager

Responsibilities:
- Mount network storage (SMB/CIFS, NFS)
- Manage mount points
- Track mounted storage status

**Note**: The current implementation provides the structure but requires elevated privileges for actual mounting. On Raspberry Pi, consider using `/etc/fstab` or `autofs` for automatic mounting.

#### Library Manager

Responsibilities:
- Scan directories for M3U playlists
- Parse M3U playlist files
- Provide playlist metadata

Features:
- Supports both M3U and M3U8 formats
- Handles relative and absolute paths in playlists
- Recursive directory scanning

#### Playback Controller

Responsibilities:
- Audio playback using pygame.mixer
- Playlist queue management
- Volume control
- Playback state tracking

Features:
- Auto-advance to next track
- Background monitoring thread
- Support for common audio formats (MP3, WAV, OGG, FLAC)

### Audio Pipeline

```mermaid
flowchart LR
    File[Audio File]
    File --> Decode[Pygame Decoder]
    Decode --> Mixer[Pygame Mixer]
    Mixer --> Buffer[Audio Buffer]
    Buffer --> ALSA[ALSA Driver]
    ALSA --> HDMI[HDMI Output]
    HDMI --> Receiver[AV Receiver]
    
    style File fill:#667eea
    style Mixer fill:#764ba2
    style HDMI fill:#4facfe
    style Receiver fill:#43e97b
```

## Data Flow

### Playback Flow

```mermaid
sequenceDiagram
    participant User
    participant UI as React UI
    participant API as Flask API
    participant PC as Playback Controller
    participant Audio as Audio System
    
    User->>UI: Click "Play" on playlist
    UI->>API: POST /api/playback/play
    API->>PC: load_playlist(path)
    PC->>PC: Parse M3U file
    PC->>Audio: Load first track
    Audio->>Audio: Initialize decoder
    PC->>Audio: Start playback
    API-->>UI: {"status": "playing"}
    UI-->>User: Update UI
    
    loop Every second
        UI->>API: GET /api/playback/status
        API->>PC: get_status()
        PC-->>API: Current track info
        API-->>UI: Status JSON
        UI-->>User: Update "Now Playing"
    end
    
    loop Background thread
        PC->>Audio: Check if playing
        Audio-->>PC: Track finished
        PC->>PC: next()
        PC->>Audio: Load next track
    end
```

### Configuration Flow

```mermaid
sequenceDiagram
    participant User
    participant UI as React UI
    participant API as Flask API
    participant Config as config.json
    
    User->>UI: Add network storage
    UI->>API: POST /api/storage
    API->>Config: Load existing config
    Config-->>API: JSON data
    API->>API: Add new storage
    API->>Config: Save updated config
    API-->>UI: New storage object
    UI-->>User: Show success
```

## Deployment Architecture

### Development Environment

```mermaid
graph TB
    Dev[Developer Machine]
    Dev --> FE[Frontend :3000]
    Dev --> BE[Backend :5000]
    FE --> Browser[Web Browser]
    BE --> FS[Local Filesystem]
    
    style Dev fill:#667eea
    style FE fill:#764ba2
    style BE fill:#f093fb
```

### Production (Raspberry Pi)

```mermaid
graph TB
    Pi[Raspberry Pi]
    Pi --> BE[Backend :5000]
    Pi --> FE[Frontend Served by Flask]
    Pi --> Audio[Audio Output]
    Audio --> HDMI[HDMI]
    HDMI --> Receiver[AV Receiver]
    
    Network[Local Network]
    Client1[Laptop]
    Client2[Phone]
    Client3[Tablet]
    
    Client1 --> Network
    Client2 --> Network
    Client3 --> Network
    Network --> BE
    
    Storage[NAS]
    Pi --> Storage
    
    style Pi fill:#667eea
    style BE fill:#764ba2
    style Audio fill:#4facfe
    style Receiver fill:#43e97b
```

## Technology Stack

### Frontend
- **Framework**: React 18 with TypeScript
- **Styling**: CSS3 with custom styles
- **HTTP Client**: Fetch API
- **Build Tool**: Create React App (Webpack under the hood)

### Backend
- **Framework**: Flask 3.0
- **CORS**: Flask-CORS
- **Audio**: Pygame 2.5
- **Metadata**: Mutagen 1.47
- **Language**: Python 3.8+

### System
- **OS**: Raspberry Pi OS (Debian-based)
- **Audio**: ALSA + HDMI
- **Network**: SMB/CIFS, NFS
- **Process Management**: systemd

## Security Considerations

### Current Implementation

⚠️ **Warning**: The current implementation is designed for private home networks and lacks security features suitable for production environments.

### Recommended Enhancements

1. **Authentication & Authorization**
   - Implement user authentication (JWT tokens)
   - Add role-based access control
   - Secure API endpoints

2. **Credential Management**
   - Encrypt stored passwords
   - Use environment variables or secrets management
   - Never commit credentials to version control

3. **Network Security**
   - Enable HTTPS with SSL certificates
   - Implement rate limiting
   - Add CSRF protection

4. **Input Validation**
   - Sanitize all user inputs
   - Validate file paths to prevent directory traversal
   - Limit file system access

5. **Deployment**
   - Run backend as non-root user
   - Use firewall rules to restrict access
   - Keep dependencies updated

## Performance Considerations

### Frontend
- **Polling Interval**: 1 second (configurable)
- **Bundle Size**: ~500KB (can be optimized with code splitting)
- **Rendering**: Virtual DOM ensures efficient updates

### Backend
- **Concurrency**: Flask development server (single-threaded)
  - For production, use Gunicorn with multiple workers
- **Audio Latency**: <100ms typical
- **Memory Usage**: ~50-100MB

### Storage
- **Network Latency**: Depends on network storage speed
- **Playlist Parsing**: O(n) where n = number of tracks
- **File System**: Standard Python I/O

## Extensibility

### Adding New Features

#### New Audio Formats
Add support in `playback_controller.py` - pygame supports most common formats through SDL2.

#### Multiple Playlists
Extend `playback_controller.py` to support queue management.

#### Audio Effects
Use pygame's sound effects or integrate external audio processing libraries.

#### Mobile App
Create a React Native app using the same API endpoints.

#### Voice Control
Integrate with voice assistants using their APIs and webhook endpoints.

## Monitoring & Logging

### Current Implementation
- Console logging with `print()` statements
- No structured logging
- No metrics collection

### Recommendations
1. Use Python's `logging` module
2. Add structured logging (JSON format)
3. Implement health check endpoint
4. Add metrics (Prometheus, StatsD)
5. Error tracking (Sentry, Rollbar)

## Backup & Recovery

### Configuration
- Backup `config.json` regularly
- Consider using configuration management (Ansible, Chef)

### Playlists
- Store playlists on network storage
- Regular backups of network storage

### System
- Create Raspberry Pi image backup
- Document setup process for quick recovery