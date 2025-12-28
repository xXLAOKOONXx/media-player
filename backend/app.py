"""
Media Player Backend
Main Flask application for media player control
"""

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename
import os
import json
import sys
import logging
from pathlib import Path


def _configure_logging() -> None:
    """Configure root logging once for console output.

    Without this, Python may default to a WARNING-level "last resort" handler,
    causing INFO logs from module loggers to never show up in the console.
    """
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return

    level_name = os.getenv('LOG_LEVEL', 'INFO').upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format='%(asctime)s %(levelname)s %(name)s: %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)],
    )

# Import modules
from storage_manager import StorageManager
from library_manager import LibraryManager
from playback_controller import PlaybackController
from sound_effects_manager import SoundEffectsManager
from music_manager import MusicManager
from audio_metadata import display_title, read_audio_metadata
from video_playback_controller import VideoPlaybackController
from video_manager import VideoManager
from database_manager import DatabaseManager

# Configure Flask to serve static files from the static folder
# Disable automatic static file serving to prevent Flask's catch-all route
# from interfering with React Router's client-side routing.
# We manually serve assets under /assets/* and use 404 handler for HTML.
static_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static'))
app = Flask(__name__, static_folder=None)

_configure_logging()

# Validate static folder exists
if not os.path.exists(static_folder):
    print(f"Warning: Static folder not found at {static_folder}")
    print("Run 'cd ../frontend && npm run build' to build the frontend")



# Initialize managers
storage_manager = StorageManager()
library_manager = LibraryManager()
sound_effects_manager = SoundEffectsManager()
music_manager = MusicManager(use_cache=True)
video_manager = VideoManager(use_cache=True)

# Initialize unified database
db = DatabaseManager()

# Legacy config file support (for migration)
CONFIG_FILE = 'config.json'

def migrate_config_to_db():
    """Migrate existing config.json to database if it exists"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                old_config = json.load(f)
            
            # Migrate each config section
            for key, value in old_config.items():
                db.set_config(key, value)
            
            # Rename the old config file as backup
            backup_file = f"{CONFIG_FILE}.migrated"
            if not os.path.exists(backup_file):
                os.rename(CONFIG_FILE, backup_file)
                print(f"Migrated config.json to database. Old file backed up as {backup_file}")
        except Exception as e:
            print(f"Warning: Failed to migrate config.json: {e}")

def load_config():
    """Load configuration from database"""
    config = db.get_all_config()
    
    # Provide defaults if not set
    if not config.get('network_storages'):
        config['network_storages'] = []
    if not config.get('libraries'):
        config['libraries'] = []
    if not config.get('crossfade'):
        config['crossfade'] = {
            'enabled': True,
            'duration_ms': 3000,
            'fade_out_start_before_end_ms': 5000
        }
    if not config.get('video'):
        config['video'] = {
            'fullscreen': True,
            'preferred_screen': None
        }
    
    return config

def save_config(config):
    """Save configuration to database"""
    for key, value in config.items():
        db.set_config(key, value)

# Migrate old config if needed
migrate_config_to_db()

# Load configuration and initialize playback controller with crossfade settings
config = load_config()
crossfade_config = config.get('crossfade', {
    'enabled': True,
    'duration_ms': 3000,
    'fade_out_start_before_end_ms': 5000
})
playback_controller = PlaybackController(crossfade_config=crossfade_config)

# Initialize video playback controller with video settings
video_config = config.get('video', {
    'fullscreen': True,
    'preferred_screen': None
})
video_playback_controller = VideoPlaybackController(video_config=video_config)

# Network Storage Management APIs
@app.route('/api/audio/storage', methods=['GET'])
def get_storages():
    """Get all configured network storages"""
    config = load_config()
    return jsonify(config.get('network_storages', []))

@app.route('/api/audio/storage', methods=['POST'])
def add_storage():
    """Add a new network storage"""
    data = request.json
    config = load_config()
    
    storage = {
        'id': len(config.get('network_storages', [])) + 1,
        'name': data.get('name'),
        'type': data.get('type', 'smb'),  # smb, nfs, etc.
        'host': data.get('host'),
        'share': data.get('share'),
        'username': data.get('username'),
        'password': data.get('password'),
        'mount_point': data.get('mount_point', f"/mnt/media_{len(config.get('network_storages', []))+1}")
    }
    
    if 'network_storages' not in config:
        config['network_storages'] = []
    config['network_storages'].append(storage)
    save_config(config)
    
    return jsonify(storage), 201

@app.route('/api/audio/storage/<int:storage_id>', methods=['DELETE'])
def delete_storage(storage_id):
    """Delete a network storage"""
    config = load_config()
    config['network_storages'] = [s for s in config.get('network_storages', []) if s['id'] != storage_id]
    save_config(config)
    return '', 204

# Playlist Management APIs
@app.route('/api/audio/playlists', methods=['GET'])
def get_playlists():
    """Get all configured playlist folders"""
    config = load_config()
    return jsonify(config.get('playlists', config.get('libraries', [])))

@app.route('/api/audio/playlists', methods=['POST'])
def add_playlist():
    """Add a new playlist folder"""
    data = request.json
    config = load_config()
    
    # Support both 'playlists' and 'libraries' keys for backward compatibility
    if 'playlists' not in config:
        config['playlists'] = config.get('libraries', [])
        if 'libraries' in config:
            del config['libraries']
    
    playlist_folder = {
        'id': len(config.get('playlists', [])) + 1,
        'name': data.get('name'),
        'type': data.get('type', 'playlist'),
        'path': data.get('path'),
        'storage_id': data.get('storage_id')
    }
    
    config['playlists'].append(playlist_folder)
    save_config(config)
    
    return jsonify(playlist_folder), 201

@app.route('/api/audio/playlists/<int:playlist_id>', methods=['PUT'])
def rename_playlist(playlist_id):
    """Rename a playlist folder"""
    data = request.json
    config = load_config()
    playlists = config.get('playlists', config.get('libraries', []))
    
    for playlist in playlists:
        if playlist['id'] == playlist_id:
            playlist['name'] = data.get('name', playlist['name'])
            config['playlists'] = playlists
            if 'libraries' in config:
                del config['libraries']
            save_config(config)
            return jsonify(playlist)
    
    return jsonify({'error': 'Playlist folder not found'}), 404

@app.route('/api/audio/playlists/<int:playlist_id>', methods=['DELETE'])
def delete_playlist(playlist_id):
    """Delete a playlist folder"""
    config = load_config()
    playlists = config.get('playlists', config.get('libraries', []))
    config['playlists'] = [p for p in playlists if p['id'] != playlist_id]
    if 'libraries' in config:
        del config['libraries']
    save_config(config)
    return '', 204

@app.route('/api/audio/playlists/<int:playlist_id>/files', methods=['GET'])
def get_playlist_files(playlist_id):
    """Get all playlist files in a folder"""
    config = load_config()
    playlists = config.get('playlists', config.get('libraries', []))
    playlist_folder = next((pf for pf in playlists if pf['id'] == playlist_id), None)
    
    if not playlist_folder:
        return jsonify({'error': 'Playlist folder not found'}), 404
    
    playlist_files = library_manager.get_playlists(playlist_folder['path'])
    return jsonify(playlist_files)

# Keep old endpoints for backward compatibility
@app.route('/api/audio/libraries', methods=['GET'])
def get_libraries():
    """Get all configured libraries (deprecated, use /api/playlists)"""
    return get_playlists()

@app.route('/api/audio/libraries', methods=['POST'])
def add_library():
    """Add a new library (deprecated, use /api/playlists)"""
    return add_playlist()

@app.route('/api/audio/libraries/<int:library_id>/playlists', methods=['GET'])
def get_playlists_old(library_id):
    """Get all playlists in a library (deprecated, use /api/playlists/<id>/files)"""
    return get_playlist_files(library_id)

@app.route('/api/audio/playlists/<int:playlist_id>/tracks', methods=['GET'])
def get_playlist_tracks(playlist_id):
    """Get all tracks in a playlist"""
    # This is a simplified implementation
    # In production, you'd need to map playlist_id to actual file
    config = load_config()
    # For now, return empty list
    return jsonify([])

# Sound Effects Management APIs
@app.route('/api/audio/soundeffects', methods=['GET'])
def get_sound_effects_folders():
    """Get all configured sound effects folders"""
    config = load_config()
    return jsonify(config.get('sound_effects', []))

@app.route('/api/audio/soundeffects', methods=['POST'])
def add_sound_effects_folder():
    """Add a new sound effects folder"""
    data = request.json
    config = load_config()
    
    if 'sound_effects' not in config:
        config['sound_effects'] = []
    
    # Generate ID based on max existing ID + 1, or 1 if no folders exist
    existing_ids = [f['id'] for f in config['sound_effects']]
    new_id = max(existing_ids) + 1 if existing_ids else 1
    
    sound_effects_folder = {
        'id': new_id,
        'name': data.get('name'),
        'path': data.get('path'),
        'storage_id': data.get('storage_id')
    }
    
    config['sound_effects'].append(sound_effects_folder)
    save_config(config)
    
    return jsonify(sound_effects_folder), 201

@app.route('/api/audio/soundeffects/<int:folder_id>', methods=['PUT'])
def rename_sound_effects_folder(folder_id):
    """Rename a sound effects folder"""
    data = request.json
    config = load_config()
    sound_effects = config.get('sound_effects', [])
    
    for folder in sound_effects:
        if folder['id'] == folder_id:
            folder['name'] = data.get('name', folder['name'])
            config['sound_effects'] = sound_effects
            save_config(config)
            return jsonify(folder)
    
    return jsonify({'error': 'Sound effects folder not found'}), 404

@app.route('/api/audio/soundeffects/<int:folder_id>', methods=['DELETE'])
def delete_sound_effects_folder(folder_id):
    """Delete a sound effects folder"""
    config = load_config()
    sound_effects = config.get('sound_effects', [])
    config['sound_effects'] = [f for f in sound_effects if f['id'] != folder_id]
    save_config(config)
    return '', 204

@app.route('/api/audio/soundeffects/<int:folder_id>/files', methods=['GET'])
def get_sound_effects_files(folder_id):
    """Get all audio files in a sound effects folder"""
    config = load_config()
    sound_effects = config.get('sound_effects', [])
    folder = next((f for f in sound_effects if f['id'] == folder_id), None)
    
    if not folder:
        return jsonify({'error': 'Sound effects folder not found'}), 404
    
    audio_files = sound_effects_manager.get_audio_files(folder['path'])
    return jsonify(audio_files)

@app.route('/api/audio/soundeffects/play', methods=['POST'])
def play_sound_effect():
    """Play a sound effect in parallel with music"""
    data = request.json
    sound_path = data.get('sound_path')
    
    if not sound_path:
        return jsonify({'error': 'sound_path is required'}), 400
    
    result = playback_controller.play_sound_effect(sound_path)
    if result:
        return jsonify({'status': 'playing', 'sound_path': sound_path})
    else:
        return jsonify({'error': 'Failed to play sound effect'}), 500

# Music Management APIs
@app.route('/api/audio/music', methods=['GET'])
def get_music_folders():
    """Get all configured music folders"""
    config = load_config()
    return jsonify(config.get('music_folders', []))

@app.route('/api/audio/music', methods=['POST'])
def add_music_folder():
    """Add a new music folder"""
    data = request.json
    config = load_config()
    
    if 'music_folders' not in config:
        config['music_folders'] = []
    
    # Generate ID based on max existing ID + 1, or 1 if no folders exist
    existing_ids = [f['id'] for f in config['music_folders']]
    new_id = max(existing_ids) + 1 if existing_ids else 1
    
    music_folder = {
        'id': new_id,
        'name': data.get('name'),
        'path': data.get('path'),
        'recursive': data.get('recursive', False),
        'storage_id': data.get('storage_id')
    }
    
    config['music_folders'].append(music_folder)
    save_config(config)
    
    return jsonify(music_folder), 201

@app.route('/api/audio/music/<int:folder_id>', methods=['PUT'])
def update_music_folder(folder_id):
    """Update a music folder"""
    data = request.json
    config = load_config()
    music_folders = config.get('music_folders', [])
    
    for folder in music_folders:
        if folder['id'] == folder_id:
            folder['name'] = data.get('name', folder['name'])
            folder['path'] = data.get('path', folder['path'])
            folder['recursive'] = data.get('recursive', folder.get('recursive', False))
            config['music_folders'] = music_folders
            save_config(config)
            return jsonify(folder)
    
    return jsonify({'error': 'Music folder not found'}), 404

@app.route('/api/audio/music/<int:folder_id>', methods=['DELETE'])
def delete_music_folder(folder_id):
    """Delete a music folder"""
    config = load_config()
    music_folders = config.get('music_folders', [])
    config['music_folders'] = [f for f in music_folders if f['id'] != folder_id]
    save_config(config)
    return '', 204

@app.route('/api/audio/music/<int:folder_id>/tracks', methods=['GET'])
def get_music_tracks(folder_id):
    """Get all tracks in a music folder with metadata"""
    config = load_config()
    music_folders = config.get('music_folders', [])
    folder = next((f for f in music_folders if f['id'] == folder_id), None)
    
    if not folder:
        return jsonify({'error': 'Music folder not found'}), 404
    
    # Check if force refresh is requested
    force_refresh = request.args.get('refresh', 'false').lower() == 'true'
    
    tracks = music_manager.get_audio_files(
        folder['path'], 
        folder.get('recursive', False),
        folder_id=folder_id,
        force_refresh=force_refresh,
        include_duration=False
    )
    return jsonify(tracks)

@app.route('/api/audio/music/<int:folder_id>/refresh', methods=['POST'])
def refresh_music_folder(folder_id):
    """Refresh/rescan a music folder and update cache"""
    config = load_config()
    music_folders = config.get('music_folders', [])
    folder = next((f for f in music_folders if f['id'] == folder_id), None)
    
    if not folder:
        return jsonify({'error': 'Music folder not found'}), 404
    
    # Force refresh - invalidate cache and rescan
    music_manager.invalidate_cache(folder_id)
    tracks = music_manager.get_audio_files(
        folder['path'],
        folder.get('recursive', False),
        folder_id=folder_id,
        force_refresh=True,
        include_duration=False
    )
    
    return jsonify({
        'success': True,
        'folder_id': folder_id,
        'track_count': len(tracks)
    })

@app.route('/api/audio/music/search', methods=['POST'])
def search_music_tracks():
    """Search tracks across all music folders by various criteria"""
    data = request.json
    
    # Get search criteria
    artist = data.get('artist')
    duration_min = data.get('duration_min')
    duration_max = data.get('duration_max')
    tags = data.get('tags')  # List of tags
    title = data.get('title')
    folder_id = data.get('folder_id')  # Optional: search in specific folder
    
    # Get all tracks from music folders
    config = load_config()
    music_folders = config.get('music_folders', [])
    
    if folder_id:
        music_folders = [f for f in music_folders if f['id'] == folder_id]
    
    all_tracks = []
    for folder in music_folders:
        tracks = music_manager.get_audio_files(
            folder['path'], 
            folder.get('recursive', False),
            folder_id=folder['id']  # Pass folder_id to enable caching
        )
        all_tracks.extend(tracks)
    
    # Apply search filters
    filtered_tracks = music_manager.search_tracks(
        all_tracks,
        artist=artist,
        duration_min=duration_min,
        duration_max=duration_max,
        tags=tags,
        title=title
    )
    
    return jsonify(filtered_tracks)

@app.route('/api/audio/music/playlists-folder', methods=['GET'])
def get_playlists_folder():
    """Get the configured playlist folder path"""
    config = load_config()
    return jsonify({'path': config.get('playlist_folder_path', '')})

@app.route('/api/audio/music/playlists-folder', methods=['PUT'])
def set_playlists_folder():
    """Set the playlist folder path"""
    data = request.json
    path = data.get('path')
    
    if not path:
        return jsonify({'error': 'path is required'}), 400
    
    config = load_config()
    config['playlist_folder_path'] = path
    save_config(config)
    
    return jsonify({'path': path})

@app.route('/api/audio/music/playlists/create', methods=['POST'])
def create_music_playlist():
    """Create a new M3U playlist from selected tracks"""
    data = request.json
    
    playlist_name = data.get('playlist_name')
    tracks = data.get('tracks', [])
    
    if not playlist_name:
        return jsonify({'error': 'playlist_name is required'}), 400
    
    if not tracks:
        return jsonify({'error': 'tracks list cannot be empty'}), 400
    
    # Get playlist folder from config
    config = load_config()
    playlist_folder = config.get('playlist_folder_path')
    
    if not playlist_folder:
        return jsonify({'error': 'Playlist folder not configured'}), 400
    
    # Create playlist file path
    playlist_filename = f"{playlist_name}.m3u"
    playlist_path = os.path.join(playlist_folder, playlist_filename)
    
    # Check if playlist already exists
    if os.path.exists(playlist_path):
        return jsonify({'error': 'Playlist already exists'}), 400
    
    # Create the playlist with relative paths
    success = music_manager.create_playlist(
        playlist_path, 
        tracks, 
        base_path=playlist_folder
    )
    
    if success:
        return jsonify({
            'success': True,
            'playlist_path': playlist_path,
            'playlist_name': playlist_name
        }), 201
    else:
        return jsonify({'error': 'Failed to create playlist'}), 500

@app.route('/api/audio/music/playlists/<path:playlist_name>/add-track', methods=['POST'])
def add_track_to_music_playlist(playlist_name):
    """Add a track to an existing playlist"""
    data = request.json
    track = data.get('track')
    
    if not track:
        return jsonify({'error': 'track is required'}), 400
    
    # Get playlist folder from config
    config = load_config()
    playlist_folder = config.get('playlist_folder_path')
    
    if not playlist_folder:
        return jsonify({'error': 'Playlist folder not configured'}), 400
    
    # Build playlist path
    playlist_path = os.path.join(playlist_folder, f"{playlist_name}.m3u")
    
    if not os.path.exists(playlist_path):
        return jsonify({'error': 'Playlist not found'}), 404
    
    # Add track to playlist
    success = music_manager.add_track_to_playlist(
        playlist_path,
        track,
        base_path=playlist_folder
    )
    
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Track already exists in playlist or failed to add'}), 400

@app.route('/api/audio/playback/add-tracks', methods=['POST'])
def add_tracks_to_current_playlist():
    """Add tracks to the current playing playlist"""
    data = request.json
    track_paths = data.get('track_paths', [])
    
    if not track_paths:
        return jsonify({'error': 'No tracks provided'}), 400
    
    # Validate that all track files exist and enrich with metadata (same tooling as Music tab)
    valid_tracks = []
    for track_path in track_paths:
        if not os.path.exists(track_path):
            print(f"Warning: Skipping non-existent track: {track_path}")
            continue

        track_obj = {'path': track_path}
        try:
            metadata = read_audio_metadata(
                track_path,
                include_duration=True,
                include_times=True,
                include_tags=False,
            )
            if isinstance(metadata, dict):
                track_obj.update(metadata)
        except Exception:
            # Best-effort: metadata is optional for playback.
            pass

        # Always apply the shared display-title fallback.
        track_obj['title'] = display_title(track_obj)
        valid_tracks.append(track_obj)
    
    if not valid_tracks:
        return jsonify({'error': 'No valid tracks found'}), 400
    
    # Add tracks to current playlist
    current_tracks = playback_controller.get_playlist_tracks()
    
    # Get existing track paths to avoid duplicates
    existing_paths = {track['path'] for track in current_tracks}
    
    # Add only new tracks
    tracks_added = 0
    for track in valid_tracks:
        if track['path'] not in existing_paths:
            playback_controller.current_playlist.append(track)
            tracks_added += 1
    
    # If shuffle is enabled, update shuffled playlist
    if playback_controller.shuffle_enabled:
        playback_controller._apply_shuffle(preserve_current=True)
    
    return jsonify({
        'success': True,
        'tracks_added': tracks_added,
        'total_tracks': len(playback_controller.current_playlist)
    })

# Playback Control APIs
@app.route('/api/audio/playback/play', methods=['POST'])
def play():
    """Start or resume playback"""
    data = request.json
    playlist_path = data.get('playlist_path')
    track_index = data.get('track_index', 0)
    
    if playlist_path:
        result = playback_controller.load_playlist(playlist_path)
        if result:
            # Best-effort: ensure duration is present for the selected track.
            # This runs on both Windows and Unix (mutagen only) and can also
            # backfill the SQLite cache when the track exists there.
            try:
                if 0 <= track_index < len(playback_controller.current_playlist):
                    track = playback_controller.current_playlist[track_index]
                    duration_val = track.get('duration')

                    has_duration = False
                    if isinstance(duration_val, (int, float)):
                        has_duration = True
                    elif isinstance(duration_val, str):
                        try:
                            float(duration_val)
                            has_duration = True
                        except ValueError:
                            has_duration = False

                    if not has_duration and track.get('path'):
                        computed = music_manager.compute_duration_seconds(track['path'])
                        if computed is not None:
                            track['duration'] = computed
                            music_manager.backfill_cached_duration(track['path'], computed)
            except Exception:
                pass

            playback_controller.play(track_index)
            return jsonify({'status': 'playing', 'track_index': track_index})
    else:
        playback_controller.resume()
        return jsonify({'status': 'playing'})
    
    return jsonify({'error': 'Invalid request'}), 400

@app.route('/api/audio/playback/pause', methods=['POST'])
def pause():
    """Pause playback"""
    playback_controller.pause()
    return jsonify({'status': 'paused'})

@app.route('/api/audio/playback/stop', methods=['POST'])
def stop():
    """Stop playback"""
    playback_controller.stop()
    return jsonify({'status': 'stopped'})

@app.route('/api/audio/playback/next', methods=['POST'])
def next_track():
    """Skip to next track"""
    playback_controller.next()
    return jsonify({'status': 'playing'})

@app.route('/api/audio/playback/previous', methods=['POST'])
def previous_track():
    """Go to previous track"""
    playback_controller.previous()
    return jsonify({'status': 'playing'})

@app.route('/api/audio/playback/volume', methods=['POST'])
def set_volume():
    """Set playback volume"""
    data = request.json
    volume = data.get('volume', 50)
    playback_controller.set_volume(volume)
    return jsonify({'volume': volume})

@app.route('/api/audio/playback/shuffle', methods=['POST'])
def set_shuffle():
    """Toggle shuffle mode"""
    data = request.json
    enabled = data.get('enabled', False)
    result = playback_controller.set_shuffle(enabled)
    return jsonify({'shuffle': enabled, 'success': result})

@app.route('/api/audio/playback/repeat', methods=['POST'])
def set_repeat():
    """Set repeat mode"""
    data = request.json
    mode = data.get('mode', 'none')
    result = playback_controller.set_repeat_mode(mode)
    if result:
        return jsonify({'repeat_mode': mode, 'success': True})
    else:
        return jsonify({'error': 'Invalid repeat mode'}), 400

@app.route('/api/audio/playback/seek', methods=['POST'])
def seek():
    """Seek to a position in the current track"""
    data = request.json
    position = data.get('position', 0)
    result = playback_controller.seek(position)
    if result:
        return jsonify({'success': True, 'position': position})
    else:
        return jsonify({'error': 'Seek failed'}), 400

@app.route('/api/audio/playback/status', methods=['GET'])
def get_status():
    """Get current playback status"""
    status = playback_controller.get_status()
    return jsonify(status)

@app.route('/api/audio/playback/tracks', methods=['GET'])
def get_tracks():
    """Get all tracks in the current playlist"""
    tracks = playback_controller.get_playlist_tracks()
    return jsonify({'tracks': tracks})

@app.route('/api/audio/playback/tracks/<int:track_index>/times', methods=['PUT'])
def set_track_times(track_index):
    """Set custom start and end times for a specific track"""
    try:
        data = request.json
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        
        # Validate input
        if start_time is not None and (not isinstance(start_time, (int, float)) or start_time < 0):
            return jsonify({'error': 'start_time must be a non-negative number'}), 400
        
        if end_time is not None and (not isinstance(end_time, (int, float)) or end_time < 0):
            return jsonify({'error': 'end_time must be a non-negative number'}), 400
        
        if start_time is not None and end_time is not None and start_time >= end_time:
            return jsonify({'error': 'start_time must be less than end_time'}), 400
        
        result = playback_controller.set_track_times(track_index, start_time, end_time)
        
        if result:
            return jsonify({'success': True, 'track_index': track_index})
        else:
            return jsonify({'error': 'Invalid track index or playlist not loaded'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Crossfade Configuration APIs
@app.route('/api/audio/crossfade/config', methods=['GET'])
def get_crossfade_config():
    """Get current crossfade configuration"""
    return jsonify(playback_controller.get_crossfade_config())

@app.route('/api/audio/crossfade/config', methods=['PUT'])
def update_crossfade_config():
    """Update crossfade configuration"""
    try:
        data = request.json
        
        # Validate input
        if 'enabled' in data and not isinstance(data['enabled'], bool):
            return jsonify({'error': 'enabled must be a boolean'}), 400
        
        if 'duration_ms' in data:
            if not isinstance(data['duration_ms'], (int, float)) or data['duration_ms'] < 0:
                return jsonify({'error': 'duration_ms must be a positive number'}), 400
        
        if 'fade_out_start_before_end_ms' in data:
            if not isinstance(data['fade_out_start_before_end_ms'], (int, float)) or data['fade_out_start_before_end_ms'] < 0:
                return jsonify({'error': 'fade_out_start_before_end_ms must be a positive number'}), 400
        
        # Update playback controller config
        playback_controller.update_crossfade_config(data)
        
        # Update and save config file
        config = load_config()
        if 'crossfade' not in config:
            config['crossfade'] = {}
        config['crossfade'].update(data)
        save_config(config)
        
        return jsonify(playback_controller.get_crossfade_config())
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# General Settings APIs
# ============================================

@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Get all application settings"""
    try:
        config = load_config()
        
        # Provide defaults for all settings
        settings = {
            'crossfade': config.get('crossfade', {
                'enabled': True,
                'duration_ms': 3000,
                'fade_out_start_before_end_ms': 5000
            }),
            'video': config.get('video', {
                'fullscreen': True,
                'preferred_screen': None
            })
        }
        
        return jsonify(settings)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings', methods=['PUT'])
def update_settings():
    """Update application settings"""
    try:
        data = request.json
        config = load_config()
        
        # Update crossfade settings if provided
        if 'crossfade' in data:
            crossfade_data = data['crossfade']
            
            # Validate crossfade input
            if 'enabled' in crossfade_data and not isinstance(crossfade_data['enabled'], bool):
                return jsonify({'error': 'crossfade.enabled must be a boolean'}), 400
            
            if 'duration_ms' in crossfade_data:
                if not isinstance(crossfade_data['duration_ms'], (int, float)) or crossfade_data['duration_ms'] < 0:
                    return jsonify({'error': 'crossfade.duration_ms must be a positive number'}), 400
            
            if 'fade_out_start_before_end_ms' in crossfade_data:
                if not isinstance(crossfade_data['fade_out_start_before_end_ms'], (int, float)) or crossfade_data['fade_out_start_before_end_ms'] < 0:
                    return jsonify({'error': 'crossfade.fade_out_start_before_end_ms must be a positive number'}), 400
            
            # Update playback controller config
            playback_controller.update_crossfade_config(crossfade_data)
            
            # Update config
            if 'crossfade' not in config:
                config['crossfade'] = {}
            config['crossfade'].update(crossfade_data)
        
        # Update video settings if provided
        if 'video' in data:
            video_data = data['video']
            
            # Validate video input
            if 'fullscreen' in video_data and not isinstance(video_data['fullscreen'], bool):
                return jsonify({'error': 'video.fullscreen must be a boolean'}), 400
            
            if 'preferred_screen' in video_data:
                if video_data['preferred_screen'] is not None and not isinstance(video_data['preferred_screen'], (int, str)):
                    return jsonify({'error': 'video.preferred_screen must be null, a number, or a string'}), 400
            
            # Update config
            if 'video' not in config:
                config['video'] = {}
            config['video'].update(video_data)
            
            # Apply video settings to video playback controller
            video_playback_controller.update_video_config(video_data)
        
        # Save config
        save_config(config)
        
        # Return updated settings
        settings = {
            'crossfade': config.get('crossfade', {}),
            'video': config.get('video', {})
        }
        
        return jsonify(settings)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# Video Management APIs
# ============================================

# Video Library Management
@app.route('/api/video/libraries', methods=['GET'])
def get_video_libraries():
    """Get all configured video libraries"""
    config = load_config()
    return jsonify(config.get('video_libraries', []))

@app.route('/api/video/libraries', methods=['POST'])
def add_video_library():
    """Add a new video library folder"""
    data = request.json
    config = load_config()
    
    if 'video_libraries' not in config:
        config['video_libraries'] = []
    
    # Generate ID
    existing_ids = [f['id'] for f in config['video_libraries']]
    new_id = max(existing_ids) + 1 if existing_ids else 1
    
    library = {
        'id': new_id,
        'name': data.get('name'),
        'path': data.get('path'),
        'recursive': data.get('recursive', False)
    }
    
    config['video_libraries'].append(library)
    save_config(config)
    
    return jsonify(library), 201

@app.route('/api/video/libraries/<int:library_id>', methods=['PUT'])
def update_video_library(library_id):
    """Update a video library"""
    data = request.json
    config = load_config()
    libraries = config.get('video_libraries', [])
    
    for lib in libraries:
        if lib['id'] == library_id:
            lib['name'] = data.get('name', lib['name'])
            config['video_libraries'] = libraries
            save_config(config)
            return jsonify(lib)
    
    return jsonify({'error': 'Video library not found'}), 404

@app.route('/api/video/libraries/<int:library_id>', methods=['DELETE'])
def delete_video_library(library_id):
    """Delete a video library"""
    config = load_config()
    libraries = config.get('video_libraries', [])
    config['video_libraries'] = [lib for lib in libraries if lib['id'] != library_id]
    save_config(config)
    
    # Invalidate cache for this library
    video_manager.invalidate_cache(library_id)
    
    return '', 204

@app.route('/api/video/libraries/<int:library_id>/videos', methods=['GET'])
def get_library_videos(library_id):
    """Get all videos in a library"""
    config = load_config()
    libraries = config.get('video_libraries', [])
    library = next((lib for lib in libraries if lib['id'] == library_id), None)
    
    if not library:
        return jsonify({'error': 'Video library not found'}), 404
    
    # Check if force refresh is requested
    force_refresh = request.args.get('refresh', '').lower() == 'true'
    
    videos = video_manager.get_video_files(
        library['path'],
        library.get('recursive', False),
        folder_id=library_id,
        force_refresh=force_refresh
    )
    return jsonify(videos)

# Video Playlist Management
@app.route('/api/video/playlists', methods=['GET'])
def get_video_playlists():
    """Get all configured video playlist folders"""
    config = load_config()
    return jsonify(config.get('video_playlists', []))

@app.route('/api/video/playlists', methods=['POST'])
def add_video_playlist_folder():
    """Add a new video playlist folder"""
    data = request.json
    config = load_config()
    
    if 'video_playlists' not in config:
        config['video_playlists'] = []
    
    existing_ids = [f['id'] for f in config['video_playlists']]
    new_id = max(existing_ids) + 1 if existing_ids else 1
    
    playlist_folder = {
        'id': new_id,
        'name': data.get('name'),
        'path': data.get('path'),
        'type': data.get('type', 'playlist')
    }
    
    config['video_playlists'].append(playlist_folder)
    save_config(config)
    
    return jsonify(playlist_folder), 201

@app.route('/api/video/playlists/<int:folder_id>', methods=['PUT'])
def update_video_playlist_folder(folder_id):
    """Update a video playlist folder"""
    data = request.json
    config = load_config()
    folders = config.get('video_playlists', [])
    
    for folder in folders:
        if folder['id'] == folder_id:
            folder['name'] = data.get('name', folder['name'])
            config['video_playlists'] = folders
            save_config(config)
            return jsonify(folder)
    
    return jsonify({'error': 'Video playlist folder not found'}), 404

@app.route('/api/video/playlists/<int:folder_id>', methods=['DELETE'])
def delete_video_playlist_folder(folder_id):
    """Delete a video playlist folder"""
    config = load_config()
    folders = config.get('video_playlists', [])
    config['video_playlists'] = [f for f in folders if f['id'] != folder_id]
    save_config(config)
    return '', 204

@app.route('/api/video/playlists/<int:folder_id>/files', methods=['GET'])
def get_video_playlist_files(folder_id):
    """Get all playlists in a folder"""
    config = load_config()
    folders = config.get('video_playlists', [])
    folder = next((f for f in folders if f['id'] == folder_id), None)
    
    if not folder:
        return jsonify({'error': 'Video playlist folder not found'}), 404
    
    playlists = library_manager.get_playlists(folder['path'])
    return jsonify(playlists)

@app.route('/api/video/playlists-folder', methods=['GET'])
def get_video_playlists_folder():
    """Get the configured video playlist folder path"""
    config = load_config()
    return jsonify({'path': config.get('video_playlist_folder_path', '')})

@app.route('/api/video/playlists-folder', methods=['PUT'])
def set_video_playlists_folder():
    """Set the video playlist folder path"""
    data = request.json
    path = data.get('path')
    
    if not path:
        return jsonify({'error': 'path is required'}), 400
    
    config = load_config()
    config['video_playlist_folder_path'] = path
    save_config(config)
    
    return jsonify({'path': path})

@app.route('/api/video/playlists/create', methods=['POST'])
def create_video_playlist():
    """Create a new M3U playlist from selected videos"""
    data = request.json
    
    playlist_name = data.get('playlist_name')
    videos = data.get('videos', [])
    
    if not playlist_name:
        return jsonify({'error': 'playlist_name is required'}), 400
    
    if not videos:
        return jsonify({'error': 'videos list cannot be empty'}), 400
    
    config = load_config()
    playlist_folder = config.get('video_playlist_folder_path')
    
    if not playlist_folder:
        return jsonify({'error': 'Video playlist folder not configured'}), 400
    
    playlist_filename = f"{playlist_name}.m3u"
    playlist_path = os.path.join(playlist_folder, playlist_filename)
    
    if os.path.exists(playlist_path):
        return jsonify({'error': 'Playlist already exists'}), 400
    
    success = video_manager.create_playlist(playlist_path, videos, base_path=playlist_folder)
    
    if success:
        return jsonify({'message': 'Playlist created successfully', 'path': playlist_path})
    else:
        return jsonify({'error': 'Failed to create playlist'}), 500

@app.route('/api/video/playlists/<playlist_name>/add-video', methods=['POST'])
def add_video_to_playlist(playlist_name):
    """Add a video to an existing playlist"""
    data = request.json
    video = data.get('video')
    
    if not video:
        return jsonify({'error': 'video is required'}), 400
    
    config = load_config()
    playlist_folder = config.get('video_playlist_folder_path')
    
    if not playlist_folder:
        return jsonify({'error': 'Video playlist folder not configured'}), 400
    
    playlist_path = os.path.join(playlist_folder, playlist_name)
    
    if not os.path.exists(playlist_path):
        return jsonify({'error': 'Playlist not found'}), 404
    
    try:
        # Append video to playlist
        with open(playlist_path, 'a', encoding='utf-8') as f:
            title = video.get('title', os.path.basename(video.get('path', '')))
            f.write(f'#EXTINF:-1,{title}\n')
            f.write(f"{video.get('path')}\n")
        
        return jsonify({'message': 'Video added to playlist successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Video Playback Control APIs
@app.route('/api/video/playback/play', methods=['POST'])
def video_play():
    """Start or resume video playback"""
    data = request.json
    
    playlist_path = data.get('playlist_path')
    track_index = data.get('track_index', 0)
    
    if playlist_path:
        success = video_playback_controller.load_playlist(playlist_path, track_index)
        if not success:
            return jsonify({'error': 'Failed to load playlist'}), 400
    
    video_playback_controller.play()
    return jsonify({'status': 'playing'})

@app.route('/api/video/playback/pause', methods=['POST'])
def video_pause():
    """Pause video playback"""
    video_playback_controller.pause()
    return jsonify({'status': 'paused'})

@app.route('/api/video/playback/stop', methods=['POST'])
def video_stop():
    """Stop video playback"""
    video_playback_controller.stop()
    return jsonify({'status': 'stopped'})

@app.route('/api/video/playback/next', methods=['POST'])
def video_next():
    """Skip to next video"""
    video_playback_controller.next_track()
    return jsonify({'status': 'ok'})

@app.route('/api/video/playback/previous', methods=['POST'])
def video_previous():
    """Skip to previous video"""
    video_playback_controller.previous_track()
    return jsonify({'status': 'ok'})

@app.route('/api/video/playback/volume', methods=['POST'])
def video_volume():
    """Set video volume"""
    data = request.json
    volume = data.get('volume', 50)
    video_playback_controller.set_volume(volume)
    return jsonify({'volume': volume})

@app.route('/api/video/playback/shuffle', methods=['POST'])
def video_shuffle():
    """Toggle shuffle mode"""
    data = request.json
    enabled = data.get('enabled', False)
    video_playback_controller.set_shuffle(enabled)
    return jsonify({'shuffle': enabled})

@app.route('/api/video/playback/repeat', methods=['POST'])
def video_repeat():
    """Set repeat mode"""
    data = request.json
    mode = data.get('mode', 'none')
    video_playback_controller.set_repeat_mode(mode)
    return jsonify({'repeat_mode': mode})

@app.route('/api/video/playback/seek', methods=['POST'])
def video_seek():
    """Seek to position in video"""
    data = request.json
    position = data.get('position', 0)
    video_playback_controller.seek(position)
    return jsonify({'position': position})

@app.route('/api/video/playback/status', methods=['GET'])
def video_status():
    """Get video playback status"""
    return jsonify(video_playback_controller.get_status())

@app.route('/api/video/playback/tracks', methods=['GET'])
def video_tracks():
    """Get current video playlist"""
    return jsonify(video_playback_controller.get_playlist())

@app.route('/api/video/playback/tracks/<int:track_index>/times', methods=['PUT'])
def update_video_track_times(track_index):
    """Update custom start/end times for a video"""
    data = request.json
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    
    success = video_playback_controller.update_track_times(track_index, start_time, end_time)
    
    if success:
        return jsonify({'status': 'ok'})
    else:
        return jsonify({'error': 'Invalid track index'}), 400

@app.route('/api/video/playback/add-videos', methods=['POST'])
def add_video_tracks():
    """Add videos to current playback playlist"""
    data = request.json
    video_paths = data.get('video_paths', [])
    
    if not video_paths:
        return jsonify({'error': 'video_paths is required'}), 400
    
    video_playback_controller.add_tracks(video_paths)
    
    return jsonify({
        'message': f'Added {len(video_paths)} video(s) to playlist',
        'playlist_length': len(video_playback_controller.get_playlist())
    })

@app.route('/api/video/stream/<path:video_path>')
def stream_video(video_path):
    """Stream a video file"""
    # Decode the video path
    video_path = '/' + video_path  # Add leading slash for absolute path
    
    if not os.path.exists(video_path):
        return jsonify({'error': 'Video not found'}), 404
    
    # Use send_from_directory for proper streaming support
    directory = os.path.dirname(video_path)
    filename = os.path.basename(video_path)
    return send_from_directory(directory, filename)

# Browse filesystem
@app.route('/api/browse', methods=['POST'])
def browse_path():
    """Browse filesystem path"""
    data = request.json
    path = data.get('path', '/')
    
    try:
        path_obj = Path(path)
        if not path_obj.exists():
            return jsonify({'error': 'Path does not exist'}), 404
        
        items = []
        for item in path_obj.iterdir():
            if not item.name.startswith('.'):
                items.append({
                    'name': item.name,
                    'path': str(item),
                    'is_directory': item.is_dir(),
                    'is_playlist': item.suffix.lower() == '.m3u' if item.is_file() else False
                })
        
        items.sort(key=lambda x: (not x['is_directory'], x['name'].lower()))
        return jsonify({'items': items, 'current_path': str(path_obj)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Serve React frontend
@app.route('/')
def serve_index():
    """Serve index.html for root path"""
    return send_from_directory(static_folder, 'index.html')

# Serve static assets (JS, CSS, images)
@app.route('/assets/<path:filename>')
def serve_assets(filename):
    """Serve static assets"""
    return send_from_directory(os.path.join(static_folder, 'assets'), filename)

@app.route('/favicon.svg')
def serve_favicon():
    """Serve favicon"""
    return send_from_directory(static_folder, 'favicon.svg')

@app.errorhandler(404)
def handle_404(e):
    """Handle 404 errors by serving React app or returning JSON for API routes"""
    # Get the request path
    path = request.path
    
    # If it's an API route, return JSON 404
    if path.startswith('/api/'):
        return jsonify({'error': 'API endpoint not found'}), 404
    
    # For all other paths, serve the React app (for client-side routing)
    index_path = os.path.join(static_folder, 'index.html')
    if os.path.exists(index_path):
        return send_from_directory(static_folder, 'index.html')
    else:
        return jsonify({
            'error': 'Frontend not built',
            'message': 'Run "cd frontend && npm run build" to build the frontend'
        }), 404

if __name__ == '__main__':
    # Development server configuration
    # WARNING: For production use, deploy with a WSGI server like Gunicorn
    # and disable debug mode. See docs/DEPLOYMENT.md for details.
    import os
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', '5000'))
    
    app.run(host=host, port=port, debug=debug_mode)
