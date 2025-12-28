# Quick Start Guide

Get the Media Player up and running in minutes!

## For Testing/Development

### Prerequisites
- Python 3.8+ installed
- Node.js 14+ installed
- Git installed

### Steps (5 minutes)

1. **Clone the repository**
   ```bash
   git clone https://github.com/xXLAOKOONXx/media-player.git
   cd media-player
   ```

2. **Install and build**
   
   **Option A: Using uv (recommended - faster):**
   ```bash
   # Backend
   cd backend
   # Install uv if needed: curl -LsSf https://astral.sh/uv/install.sh | sh
   uv venv && source .venv/bin/activate
   uv pip install -e .
   
   # Frontend
   cd ../frontend
   npm install
   npm run build
   
   # Start application
   cd ../backend
   python3 app.py
   ```
   
   **Option B: Using pip:**
   ```bash
   # Backend
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e .
   
   # Frontend
   cd ../frontend
   npm install
   npm run build
   
   # Start application
   cd ../backend
   python3 app.py
   ```
   
   Application is now running at `http://localhost:5000`

3. **Use the application**
   - Navigate to `http://localhost:5000` in your browser
   - Click on the **Storage** tab to configure network storage
   - Switch to **Library** tab to add your playlist folders
   - Go to **Player** tab to control playback

### Development Mode (Frontend Hot Reload)

If you want to make frontend changes with live reload:

```bash
# Terminal 1 - Backend
cd backend
python3 app.py

# Terminal 2 - Frontend dev server
cd frontend
npm run dev
```

Access at `http://localhost:5173` for hot reload development.

## For Raspberry Pi (Production)

### Prerequisites
- Raspberry Pi 3 or newer
- Raspberry Pi OS installed
- SSH access enabled
- HDMI cable to audio receiver

### Steps (30 minutes)

1. **Connect via SSH**
   ```bash
   ssh pi@raspberrypi.local
   ```

2. **Update system**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

3. **Install dependencies**
   ```bash
   sudo apt install -y python3 python3-venv git curl ca-certificates nodejs npm

   # Install uv
   curl -LsSf https://astral.sh/uv/install.sh | sh
   export PATH="$HOME/.local/bin:$PATH"
   ```

4. **Clone and setup**
   ```bash
   cd ~
   git clone https://github.com/xXLAOKOONXx/media-player.git
   cd media-player
   
   # Backend
   cd backend
   uv venv
   source .venv/bin/activate
   uv pip install -e .
   
   # Frontend
   cd ../frontend
   npm install
   npm run build
   ```

5. **Configure audio to HDMI**
   ```bash
   sudo raspi-config
   # Navigate to: System Options -> Audio -> HDMI
   ```

6. **Install as service**
   ```bash
   sudo cp ~/media-player/examples/mediaplayer.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable mediaplayer
   sudo systemctl start mediaplayer
   ```

7. **Access the UI**
   - From any device on your network: `http://raspberrypi.local:5000`
   - Or use the IP address: `http://192.168.1.xxx:5000`

## First Time Setup

### 1. Configure Network Storage

1. Click **Storage** tab
2. Click **+ Add Storage**
3. Fill in:
   - Name: "My NAS"
   - Type: SMB/CIFS
   - Host: Your NAS IP (e.g., 192.168.1.10)
   - Share: Share name (e.g., "music")
   - Username/Password: Your credentials
4. Click **Add Storage**

### 2. Add a Library

1. Click **Library** tab
2. Click **+ Add Library**
3. Fill in:
   - Name: "Playlists"
   - Path: Path to your playlist folder
4. Click **Browse** to navigate your filesystem
5. Click **Add Library**

### 3. Play Music

1. Select your library from the list
2. Click **Play** on any playlist
3. Switch to **Player** tab to see now playing
4. Use controls to play/pause/skip/adjust volume

## Troubleshooting

### Backend won't start

```bash
# Check Python version
python3 --version  # Should be 3.8+

# Reinstall dependencies
cd backend
source .venv/bin/activate
uv pip install -e . --upgrade
```

### Frontend won't start

```bash
# Clear cache and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### No audio on Raspberry Pi

```bash
# Test audio
speaker-test -t wav -c 2

# Check HDMI connection
/usr/bin/tvservice -s

# Set audio output
sudo raspi-config
# System Options -> Audio -> HDMI
```

### Can't access from other devices

```bash
# Check if service is running
sudo systemctl status mediaplayer

# Check firewall (if enabled)
sudo ufw status
sudo ufw allow from 192.168.1.0/24 to any port 5000

# Find your IP
hostname -I
```

## Next Steps

- 📖 Read the full [README](../README.md)
- 🏗️ Learn about the [Architecture](ARCHITECTURE.md)
- 🍓 Follow the complete [Raspberry Pi Setup Guide](RASPBERRY_PI_SETUP.md)
- 🚀 Check out [Deployment options](DEPLOYMENT.md)
- 🔒 Review [Security considerations](SECURITY.md)
- 📡 Explore the [API documentation](API.md)

## Need Help?

- Open an issue on GitHub
- Check the troubleshooting sections in the documentation
- Review the examples in the `examples/` directory

## Tips

💡 **Use relative paths in playlists** - If your playlist and audio files are in the same directory structure, use relative paths for portability.

💡 **Organize your music** - Keep playlists in a dedicated folder for easy management.

💡 **Test with small playlists first** - Verify everything works before loading large libraries.

💡 **Keep backups** - Regularly backup your `config.json` file.

💡 **Monitor the logs** - Use `sudo journalctl -u mediaplayer -f` to watch service logs on Raspberry Pi.

Enjoy your media player! 🎵