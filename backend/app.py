"""
Media Player Backend
Main Flask application for media player control
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import json
from pathlib import Path

# Import modules
from storage_manager import StorageManager
from library_manager import LibraryManager
from playback_controller import PlaybackController

# Configure Flask to serve static files from the static folder
# Use absolute path for security
static_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static'))
app = Flask(__name__, static_folder=static_folder, static_url_path='')

# Validate static folder exists
if not os.path.exists(static_folder):
    print(f"Warning: Static folder not found at {static_folder}")
    print("Run 'cd ../frontend && npm run build' to build the frontend")

# Enable CORS for development (when frontend runs on different port)
# In production, frontend is served from Flask, so CORS not needed
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Initialize managers
storage_manager = StorageManager()
library_manager = LibraryManager()
playback_controller = PlaybackController()

# Configuration
CONFIG_FILE = 'config.json'

def load_config():
    """Load configuration from file"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {'network_storages': [], 'libraries': []}

def save_config(config):
    """Save configuration to file"""
    # Note: In production, consider encrypting sensitive data like passwords
    # or using environment variables and secure credential storage
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

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

# Library Management APIs
@app.route('/api/libraries', methods=['GET'])
def get_libraries():
    """Get all configured libraries"""
    config = load_config()
    return jsonify(config.get('libraries', []))

@app.route('/api/libraries', methods=['POST'])
def add_library():
    """Add a new library"""
    data = request.json
    config = load_config()
    
    library = {
        'id': len(config.get('libraries', [])) + 1,
        'name': data.get('name'),
        'type': data.get('type', 'playlist'),  # playlist, music, etc.
        'path': data.get('path'),
        'storage_id': data.get('storage_id')
    }
    
    if 'libraries' not in config:
        config['libraries'] = []
    config['libraries'].append(library)
    save_config(config)
    
    return jsonify(library), 201

@app.route('/api/libraries/<int:library_id>/playlists', methods=['GET'])
def get_playlists(library_id):
    """Get all playlists in a library"""
    config = load_config()
    libraries = config.get('libraries', [])
    library = next((lib for lib in libraries if lib['id'] == library_id), None)
    
    if not library:
        return jsonify({'error': 'Library not found'}), 404
    
    playlists = library_manager.get_playlists(library['path'])
    return jsonify(playlists)

@app.route('/api/playlists/<int:playlist_id>/tracks', methods=['GET'])
def get_playlist_tracks(playlist_id):
    """Get all tracks in a playlist"""
    # This is a simplified implementation
    # In production, you'd need to map playlist_id to actual file
    config = load_config()
    # For now, return empty list
    return jsonify([])

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

@app.route('/api/playback/status', methods=['GET'])
def get_status():
    """Get current playback status"""
    status = playback_controller.get_status()
    return jsonify(status)

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
