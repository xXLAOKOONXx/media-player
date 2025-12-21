"""
Media Player Backend
Main Flask application for media player control
"""

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename
import os
import json
from pathlib import Path

# Import modules
from storage_manager import StorageManager
from library_manager import LibraryManager
from playback_controller import PlaybackController
from sound_effects_manager import SoundEffectsManager
from music_manager import MusicManager

# Configure Flask to serve static files from the static folder
# Use absolute path for security
static_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static'))
app = Flask(__name__, static_folder=static_folder, static_url_path='')

# Validate static folder exists
if not os.path.exists(static_folder):
    print(f"Warning: Static folder not found at {static_folder}")
    print("Run 'cd ../frontend && npm run build' to build the frontend")



# Initialize managers
storage_manager = StorageManager()
library_manager = LibraryManager()
sound_effects_manager = SoundEffectsManager()
music_manager = MusicManager(use_cache=True)

# Configuration
CONFIG_FILE = 'config.json'

def load_config():
    """Load configuration from file"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {
        'network_storages': [],
        'libraries': [],
        'crossfade': {
            'enabled': True,
            'duration_ms': 3000,
            'fade_out_start_before_end_ms': 5000
        }
    }

def save_config(config):
    """Save configuration to file"""
    # Note: In production, consider encrypting sensitive data like passwords
    # or using environment variables and secure credential storage
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

# Load configuration and initialize playback controller with crossfade settings
config = load_config()
crossfade_config = config.get('crossfade', {
    'enabled': True,
    'duration_ms': 3000,
    'fade_out_start_before_end_ms': 5000
})
playback_controller = PlaybackController(crossfade_config=crossfade_config)

# Network Storage Management APIs
@app.route('/api/storage', methods=['GET'])
def get_storages():
    """Get all configured network storages"""
    config = load_config()
    return jsonify(config.get('network_storages', []))

@app.route('/api/storage', methods=['POST'])
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

@app.route('/api/storage/<int:storage_id>', methods=['DELETE'])
def delete_storage(storage_id):
    """Delete a network storage"""
    config = load_config()
    config['network_storages'] = [s for s in config.get('network_storages', []) if s['id'] != storage_id]
    save_config(config)
    return '', 204

# Playlist Management APIs
@app.route('/api/playlists', methods=['GET'])
def get_playlists():
    """Get all configured playlist folders"""
    config = load_config()
    return jsonify(config.get('playlists', config.get('libraries', [])))

@app.route('/api/playlists', methods=['POST'])
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

@app.route('/api/playlists/<int:playlist_id>', methods=['PUT'])
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

@app.route('/api/playlists/<int:playlist_id>', methods=['DELETE'])
def delete_playlist(playlist_id):
    """Delete a playlist folder"""
    config = load_config()
    playlists = config.get('playlists', config.get('libraries', []))
    config['playlists'] = [p for p in playlists if p['id'] != playlist_id]
    if 'libraries' in config:
        del config['libraries']
    save_config(config)
    return '', 204

@app.route('/api/playlists/<int:playlist_id>/files', methods=['GET'])
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
@app.route('/api/libraries', methods=['GET'])
def get_libraries():
    """Get all configured libraries (deprecated, use /api/playlists)"""
    return get_playlists()

@app.route('/api/libraries', methods=['POST'])
def add_library():
    """Add a new library (deprecated, use /api/playlists)"""
    return add_playlist()

@app.route('/api/libraries/<int:library_id>/playlists', methods=['GET'])
def get_playlists_old(library_id):
    """Get all playlists in a library (deprecated, use /api/playlists/<id>/files)"""
    return get_playlist_files(library_id)

@app.route('/api/playlists/<int:playlist_id>/tracks', methods=['GET'])
def get_playlist_tracks(playlist_id):
    """Get all tracks in a playlist"""
    # This is a simplified implementation
    # In production, you'd need to map playlist_id to actual file
    config = load_config()
    # For now, return empty list
    return jsonify([])

# Sound Effects Management APIs
@app.route('/api/soundeffects', methods=['GET'])
def get_sound_effects_folders():
    """Get all configured sound effects folders"""
    config = load_config()
    return jsonify(config.get('sound_effects', []))

@app.route('/api/soundeffects', methods=['POST'])
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

@app.route('/api/soundeffects/<int:folder_id>', methods=['PUT'])
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

@app.route('/api/soundeffects/<int:folder_id>', methods=['DELETE'])
def delete_sound_effects_folder(folder_id):
    """Delete a sound effects folder"""
    config = load_config()
    sound_effects = config.get('sound_effects', [])
    config['sound_effects'] = [f for f in sound_effects if f['id'] != folder_id]
    save_config(config)
    return '', 204

@app.route('/api/soundeffects/<int:folder_id>/files', methods=['GET'])
def get_sound_effects_files(folder_id):
    """Get all audio files in a sound effects folder"""
    config = load_config()
    sound_effects = config.get('sound_effects', [])
    folder = next((f for f in sound_effects if f['id'] == folder_id), None)
    
    if not folder:
        return jsonify({'error': 'Sound effects folder not found'}), 404
    
    audio_files = sound_effects_manager.get_audio_files(folder['path'])
    return jsonify(audio_files)

@app.route('/api/soundeffects/play', methods=['POST'])
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
@app.route('/api/music', methods=['GET'])
def get_music_folders():
    """Get all configured music folders"""
    config = load_config()
    return jsonify(config.get('music_folders', []))

@app.route('/api/music', methods=['POST'])
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

@app.route('/api/music/<int:folder_id>', methods=['PUT'])
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

@app.route('/api/music/<int:folder_id>', methods=['DELETE'])
def delete_music_folder(folder_id):
    """Delete a music folder"""
    config = load_config()
    music_folders = config.get('music_folders', [])
    config['music_folders'] = [f for f in music_folders if f['id'] != folder_id]
    save_config(config)
    return '', 204

@app.route('/api/music/<int:folder_id>/tracks', methods=['GET'])
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

@app.route('/api/music/<int:folder_id>/refresh', methods=['POST'])
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

@app.route('/api/music/search', methods=['POST'])
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

@app.route('/api/music/playlists-folder', methods=['GET'])
def get_playlists_folder():
    """Get the configured playlist folder path"""
    config = load_config()
    return jsonify({'path': config.get('playlist_folder_path', '')})

@app.route('/api/music/playlists-folder', methods=['PUT'])
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

@app.route('/api/music/playlists/create', methods=['POST'])
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

@app.route('/api/music/playlists/<path:playlist_name>/add-track', methods=['POST'])
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

@app.route('/api/playback/add-tracks', methods=['POST'])
def add_tracks_to_current_playlist():
    """Add tracks to the current playing playlist"""
    data = request.json
    track_paths = data.get('track_paths', [])
    
    if not track_paths:
        return jsonify({'error': 'No tracks provided'}), 400
    
    # Validate that all track files exist
    valid_tracks = []
    for track_path in track_paths:
        if os.path.exists(track_path):
            valid_tracks.append({'path': track_path})
        else:
            print(f"Warning: Skipping non-existent track: {track_path}")
    
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
@app.route('/api/playback/play', methods=['POST'])
def play():
    """Start or resume playback"""
    data = request.json
    playlist_path = data.get('playlist_path')
    track_index = data.get('track_index', 0)
    
    if playlist_path:
        result = playback_controller.load_playlist(playlist_path)
        if result:
            playback_controller.play(track_index)
            return jsonify({'status': 'playing', 'track_index': track_index})
    else:
        playback_controller.resume()
        return jsonify({'status': 'playing'})
    
    return jsonify({'error': 'Invalid request'}), 400

@app.route('/api/playback/pause', methods=['POST'])
def pause():
    """Pause playback"""
    playback_controller.pause()
    return jsonify({'status': 'paused'})

@app.route('/api/playback/stop', methods=['POST'])
def stop():
    """Stop playback"""
    playback_controller.stop()
    return jsonify({'status': 'stopped'})

@app.route('/api/playback/next', methods=['POST'])
def next_track():
    """Skip to next track"""
    playback_controller.next()
    return jsonify({'status': 'playing'})

@app.route('/api/playback/previous', methods=['POST'])
def previous_track():
    """Go to previous track"""
    playback_controller.previous()
    return jsonify({'status': 'playing'})

@app.route('/api/playback/volume', methods=['POST'])
def set_volume():
    """Set playback volume"""
    data = request.json
    volume = data.get('volume', 50)
    playback_controller.set_volume(volume)
    return jsonify({'volume': volume})

@app.route('/api/playback/shuffle', methods=['POST'])
def set_shuffle():
    """Toggle shuffle mode"""
    data = request.json
    enabled = data.get('enabled', False)
    result = playback_controller.set_shuffle(enabled)
    return jsonify({'shuffle': enabled, 'success': result})

@app.route('/api/playback/repeat', methods=['POST'])
def set_repeat():
    """Set repeat mode"""
    data = request.json
    mode = data.get('mode', 'none')
    result = playback_controller.set_repeat_mode(mode)
    if result:
        return jsonify({'repeat_mode': mode, 'success': True})
    else:
        return jsonify({'error': 'Invalid repeat mode'}), 400

@app.route('/api/playback/seek', methods=['POST'])
def seek():
    """Seek to a position in the current track"""
    data = request.json
    position = data.get('position', 0)
    result = playback_controller.seek(position)
    if result:
        return jsonify({'success': True, 'position': position})
    else:
        return jsonify({'error': 'Seek failed'}), 400

@app.route('/api/playback/status', methods=['GET'])
def get_status():
    """Get current playback status"""
    status = playback_controller.get_status()
    return jsonify(status)

@app.route('/api/playback/tracks', methods=['GET'])
def get_tracks():
    """Get all tracks in the current playlist"""
    tracks = playback_controller.get_playlist_tracks()
    return jsonify({'tracks': tracks})

@app.route('/api/playback/tracks/<int:track_index>/times', methods=['PUT'])
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
@app.route('/api/crossfade/config', methods=['GET'])
def get_crossfade_config():
    """Get current crossfade configuration"""
    return jsonify(playback_controller.get_crossfade_config())

@app.route('/api/crossfade/config', methods=['PUT'])
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
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    """Serve the React frontend or API 404"""
    # If path starts with 'api', it's an API route that wasn't found
    if path.startswith('api/'):
        return jsonify({'error': 'API endpoint not found'}), 404
    
    # Sanitize path to prevent directory traversal
    if path:
        # Remove any directory traversal attempts
        path = path.replace('..', '')
        # Normalize the path
        safe_path = os.path.normpath(path).lstrip('/')
        full_path = os.path.join(app.static_folder, safe_path)
        
        # Ensure the file is within static folder (prevent directory traversal)
        if os.path.commonpath([app.static_folder, full_path]) != app.static_folder:
            return jsonify({'error': 'Invalid path'}), 400
        
        # Check if file exists and serve it
        if os.path.isfile(full_path):
            return send_from_directory(app.static_folder, safe_path)
    
    # Otherwise, serve index.html (for React Router)
    index_path = os.path.join(app.static_folder, 'index.html')
    if os.path.exists(index_path):
        return send_from_directory(app.static_folder, 'index.html')
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
