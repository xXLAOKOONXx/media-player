# Deployment Guide

This guide covers deploying the Media Player application in different environments.

## Table of Contents

1. [Development Deployment](#development-deployment)
2. [Production Deployment on Raspberry Pi](#production-deployment-on-raspberry-pi)
3. [Bundled Distribution](#bundled-distribution)
4. [Docker Deployment](#docker-deployment-future)
5. [Reverse Proxy Setup](#reverse-proxy-setup)
6. [Security Considerations](#security-considerations)

## Development Deployment

### Prerequisites

- Python 3.8+
- Node.js 14+
- Git

### Steps

1. **Clone and install**
   ```bash
   git clone https://github.com/xXLAOKOONXx/media-player.git
   cd media-player
   
   # Backend
   cd backend
   # Install uv if needed: curl -LsSf https://astral.sh/uv/install.sh | sh
   uv venv
   source .venv/bin/activate
   uv pip install -e .
   
   # Frontend
   cd ../frontend
   npm install
   ```

2. **Start services**
   ```bash
   # Terminal 1 - Backend
   cd backend
   python3 app.py
   
   # Terminal 2 - Frontend
   cd frontend
   npm run dev
   ```

3. **Access**
   - Frontend (dev): http://localhost:5173
   - Backend API: http://localhost:5000

## Production Deployment on Raspberry Pi

### Full Setup

Follow the [Raspberry Pi Setup Guide](RASPBERRY_PI_SETUP.md) for complete instructions.

### Quick Deployment

1. **Prepare the system**
   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install -y python3 python3-venv git curl ca-certificates nodejs npm

   # Install uv
   curl -LsSf https://astral.sh/uv/install.sh | sh
   export PATH="$HOME/.local/bin:$PATH"
   ```

2. **Clone and setup**
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

3. **Install systemd service**
   ```bash
   # Copy service file
   sudo cp examples/mediaplayer.service /etc/systemd/system/
   
   # Adjust paths if needed
   sudo nano /etc/systemd/system/mediaplayer.service
   
   # Enable and start
   sudo systemctl daemon-reload
   sudo systemctl enable mediaplayer
   sudo systemctl start mediaplayer
   
   # Check status
   sudo systemctl status mediaplayer
   ```

4. **Serve frontend**

   The frontend build outputs into `backend/static` and is served by the Flask backend on port 5000.

### Systemd Service Management

```bash
# View logs
sudo journalctl -u mediaplayer -f

# Restart service
sudo systemctl restart mediaplayer

# Stop service
sudo systemctl stop mediaplayer

# Disable auto-start
sudo systemctl disable mediaplayer
```

## Bundled Distribution

For distributing the application as standalone bundles with built frontend:

### Windows Executable Bundle

Create a standalone executable using PyInstaller:

```bash
# On Windows
build.bat
```

The bundle will be created in `backend/dist/media-player/` and can be distributed to users without requiring Python installation.

### Unix Distribution Package

Create a distribution package for Linux/macOS:

```bash
# On Linux/macOS
./build.sh
```

The package will be created in `dist/media-player-unix/` and includes all necessary files with installation instructions.

### Benefits

- **Pre-built Frontend**: All bundles include the built React frontend
- **Easy Distribution**: Share a single folder with users
- **No Build Steps**: Users don't need Node.js or build tools
- **Platform-Specific**: Optimized for each platform

For detailed bundling instructions, see the [Bundling Guide](BUNDLING.md).

## Docker Deployment (Future)

Docker support is planned for future releases. This will simplify deployment across different platforms.

### Planned Features

- Multi-stage build for optimized image size
- Docker Compose for easy orchestration
- Volume mounts for configuration and media
- Health checks
- Support for arm64 (Raspberry Pi)

## Reverse Proxy Setup

### Using Nginx

1. **Install nginx**
   ```bash
   sudo apt install -y nginx
   ```

2. **Create site configuration**
   ```bash
   sudo nano /etc/nginx/sites-available/mediaplayer
   ```

3. **Configuration**
   ```nginx
   server {
       listen 80;
       server_name mediaplayer.local;
       
       # Frontend
       location / {
           root /home/pi/media-player/frontend/build;
           index index.html;
           try_files $uri $uri/ /index.html;
       }
       
       # Backend API
       location /api {
           proxy_pass http://127.0.0.1:5000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection 'upgrade';
           proxy_set_header Host $host;
           proxy_cache_bypass $http_upgrade;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       }
   }
   ```

4. **Enable and restart**
   ```bash
   sudo ln -s /etc/nginx/sites-available/mediaplayer /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

5. **Update frontend configuration**
   
   Edit `frontend/.env.production`:
   ```
   REACT_APP_API_URL=http://mediaplayer.local
   ```
   
   Rebuild frontend:
   ```bash
   cd frontend
   npm run build
   ```

### Using Apache

1. **Install Apache**
   ```bash
   sudo apt install -y apache2
   sudo a2enmod proxy proxy_http rewrite
   ```

2. **Create virtual host**
   ```bash
   sudo nano /etc/apache2/sites-available/mediaplayer.conf
   ```

3. **Configuration**
   ```apache
   <VirtualHost *:80>
       ServerName mediaplayer.local
       
       DocumentRoot /home/pi/media-player/frontend/build
       
       <Directory /home/pi/media-player/frontend/build>
           Options -Indexes +FollowSymLinks
           AllowOverride All
           Require all granted
           
           # Rewrite for React Router
           RewriteEngine On
           RewriteBase /
           RewriteRule ^index\.html$ - [L]
           RewriteCond %{REQUEST_FILENAME} !-f
           RewriteCond %{REQUEST_FILENAME} !-d
           RewriteRule . /index.html [L]
       </Directory>
       
       # Proxy API requests
       ProxyPass /api http://127.0.0.1:5000/api
       ProxyPassReverse /api http://127.0.0.1:5000/api
       
       ErrorLog ${APACHE_LOG_DIR}/mediaplayer-error.log
       CustomLog ${APACHE_LOG_DIR}/mediaplayer-access.log combined
   </VirtualHost>
   ```

4. **Enable and restart**
   ```bash
   sudo a2ensite mediaplayer
   sudo systemctl restart apache2
   ```

## Security Considerations

### Production Checklist

- [ ] Change default Flask secret key
- [ ] Enable HTTPS with SSL certificates (Let's Encrypt)
- [ ] Implement authentication and authorization
- [ ] Use environment variables for sensitive data
- [ ] Enable firewall (ufw)
- [ ] Keep software updated
- [ ] Regular backups
- [ ] Secure network storage credentials
- [ ] Run services as non-root user
- [ ] Implement rate limiting

### HTTPS Setup with Let's Encrypt

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d mediaplayer.yourdomain.com

# Auto-renewal is configured automatically
sudo certbot renew --dry-run
```

### Firewall Configuration

```bash
# Install and enable ufw
sudo apt install -y ufw

# Allow SSH (important!)
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Or allow only from local network
sudo ufw allow from 192.168.1.0/24 to any port 80
sudo ufw allow from 192.168.1.0/24 to any port 443

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

### Environment Variables

For production, use environment variables instead of hardcoding values:

```bash
# Create .env file
nano ~/media-player/backend/.env
```

Content:
```bash
FLASK_SECRET_KEY=your-secret-key-here
API_PORT=5000
DEBUG=False
```

Update `app.py` to read from environment:
```python
import os
from dotenv import load_dotenv

load_dotenv()

app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-key')
```

## Performance Optimization

### Backend

1. **Use Gunicorn for production**
   ```bash
   cd ~/media-player/backend
   source .venv/bin/activate
   uv pip install gunicorn
   .venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

2. **Update systemd service**
   ```ini
   ExecStart=/home/pi/media-player/backend/.venv/bin/gunicorn -w 2 -b 127.0.0.1:5000 app:app
   ```

### Frontend

1. **Optimize build**
   ```bash
   npm run build
   ```

2. **Enable gzip compression in nginx**
   ```nginx
   gzip on;
   gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
   ```

3. **Add caching headers**
   ```nginx
   location /static {
       expires 1y;
       add_header Cache-Control "public, immutable";
   }
   ```

## Monitoring

### System Monitoring

```bash
# Check service status
sudo systemctl status mediaplayer

# View logs
sudo journalctl -u mediaplayer -f

# Check resource usage
htop
```

### Application Monitoring

Add health check endpoint in `app.py`:
```python
@app.route('/health')
def health():
    return jsonify({'status': 'healthy'}), 200
```

Monitor with cron:
```bash
crontab -e

# Add:
*/5 * * * * curl -f http://localhost:5000/health || systemctl restart mediaplayer
```

## Backup Strategy

### Configuration Backup

```bash
# Create backup script
cat > ~/backup-mediaplayer.sh << 'EOF'
#!/bin/bash
BACKUP_DIR=~/mediaplayer-backups
mkdir -p $BACKUP_DIR
DATE=$(date +%Y%m%d_%H%M%S)

# Backup config
cp ~/media-player/backend/config.json $BACKUP_DIR/config_$DATE.json

# Keep only last 7 days
find $BACKUP_DIR -name "config_*.json" -mtime +7 -delete
EOF

chmod +x ~/backup-mediaplayer.sh

# Add to crontab
crontab -e
# Add: 0 2 * * * ~/backup-mediaplayer.sh
```

### Full System Backup

For Raspberry Pi, create SD card image periodically:
```bash
# On Linux PC with SD card reader
sudo dd if=/dev/sdX of=~/mediaplayer-backup.img bs=4M status=progress
```

## Troubleshooting Deployment

### Service Won't Start

```bash
# Check service status
sudo systemctl status mediaplayer

# View recent logs
sudo journalctl -u mediaplayer -n 50

# Check permissions
ls -la /home/pi/media-player/backend

# Test manual start
cd /home/pi/media-player/backend
python3 app.py
```

### Frontend Not Loading

```bash
# Check if build exists
ls -la /home/pi/media-player/backend/static

# Check nginx/apache logs
sudo tail -f /var/log/nginx/error.log

# Test direct file access
curl -I http://localhost:80
```

### API Connection Issues

```bash
# Test backend
curl http://localhost:5000/api/playback/status

# Check CORS configuration
curl -H "Origin: http://localhost:5173" \
     -H "Access-Control-Request-Method: GET" \
     -X OPTIONS \
     http://localhost:5000/api/playback/status

# Check firewall
sudo ufw status
```

## Updating the Application

```bash
# Stop service
sudo systemctl stop mediaplayer

# Backup configuration
cp ~/media-player/backend/config.json ~/config.json.backup

# Pull updates
cd ~/media-player
git pull

# Update dependencies
cd backend
source .venv/bin/activate
uv pip install -e .

cd ../frontend
npm install
npm run build

# Restore configuration if needed
cp ~/config.json.backup ~/media-player/backend/config.json

# Start service
sudo systemctl start mediaplayer
sudo systemctl status mediaplayer
```

## Additional Resources

- [Raspberry Pi Setup Guide](RASPBERRY_PI_SETUP.md)
- [Architecture Documentation](ARCHITECTURE.md)
- [API Documentation](API.md)
- [Main README](../README.md)