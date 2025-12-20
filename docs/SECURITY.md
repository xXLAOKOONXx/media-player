# Security Considerations

## ⚠️ Important Security Notice

This application is designed for use on private home networks and includes several areas that require hardening for production use.

## Current Security Status

### Development Mode
- ✅ Suitable for local development and testing
- ✅ Safe for use on private home networks
- ⚠️ **NOT RECOMMENDED** for public internet exposure without modifications

## Security Issues and Recommendations

### 1. Credential Storage

**Issue**: Network storage passwords are stored in plain text in `config.json`

**Recommendations**:
```bash
# Option 1: Use environment variables
export NAS_PASSWORD="your_password"

# Option 2: Use encrypted credentials file
# Create credentials file
echo "username=user" > ~/.smbcredentials
echo "password=pass" >> ~/.smbcredentials
chmod 600 ~/.smbcredentials

# Option 3: Use system keyring (Linux)
secret-tool store --label="NAS Password" service mediaplayer username user
```

**Implementation**:
```python
import os
from cryptography.fernet import Fernet

# Encrypt sensitive data before saving
def encrypt_password(password, key):
    f = Fernet(key)
    return f.encrypt(password.encode()).decode()

def decrypt_password(encrypted_password, key):
    f = Fernet(key)
    return f.decrypt(encrypted_password.encode()).decode()
```

### 2. No Authentication

**Issue**: Web interface and API have no authentication

**Recommendations**:
```python
# Add Flask-Login or Flask-JWT-Extended
from flask_login import LoginManager, login_required

# Protect routes
@app.route('/api/playback/play', methods=['POST'])
@login_required
def play():
    # ...
```

### 3. CORS Configuration

**Issue**: CORS is enabled for all origins

**Current**:
```python
CORS(app)  # Allows all origins
```

**Recommended**:
```python
from flask_cors import CORS

# Restrict to specific origins
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "http://raspberrypi.local"],
        "methods": ["GET", "POST", "DELETE"],
        "allow_headers": ["Content-Type"]
    }
})
```

### 4. Debug Mode

**Issue**: Debug mode enabled by default

**Fix**: Use environment variables
```bash
# .env file
FLASK_DEBUG=False
FLASK_HOST=127.0.0.1  # Only localhost in production
FLASK_PORT=5000
```

### 5. Input Validation

**Issue**: Limited input validation on API endpoints

**Recommendations**:
```python
from flask import request
from werkzeug.utils import secure_filename
import os

@app.route('/api/browse', methods=['POST'])
def browse_path():
    data = request.json
    path = data.get('path', '/')
    
    # Validate path to prevent directory traversal
    path = os.path.abspath(path)
    if not path.startswith('/mnt/'):
        return jsonify({'error': 'Invalid path'}), 400
    
    # ... rest of implementation
```

### 6. SQL Injection (Future)

If you add a database:
```python
# BAD - Never do this
query = f"SELECT * FROM playlists WHERE name = '{name}'"

# GOOD - Use parameterized queries
cursor.execute("SELECT * FROM playlists WHERE name = ?", (name,))
```

### 7. HTTPS/TLS

**Issue**: No HTTPS encryption

**Setup with nginx**:
```nginx
server {
    listen 443 ssl http2;
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # Strong SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
    ssl_prefer_server_ciphers on;
}
```

### 8. Rate Limiting

**Issue**: No rate limiting on API endpoints

**Implementation**:
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/api/playback/play', methods=['POST'])
@limiter.limit("10 per minute")
def play():
    # ...
```

### 9. Secure Headers

**Add security headers**:
```python
@app.after_request
def set_secure_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response
```

### 10. Logging

**Issue**: Minimal logging of security events

**Recommendations**:
```python
import logging
from logging.handlers import RotatingFileHandler

# Configure logging
handler = RotatingFileHandler('mediaplayer.log', maxBytes=10000000, backupCount=5)
handler.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
app.logger.addHandler(handler)

# Log security events
@app.route('/api/playback/play', methods=['POST'])
def play():
    app.logger.info(f"Playback started from IP: {request.remote_addr}")
    # ...
```

## Security Checklist for Production

- [ ] Enable HTTPS with valid SSL certificate
- [ ] Implement user authentication
- [ ] Add authorization/access control
- [ ] Encrypt stored credentials
- [ ] Configure CORS properly
- [ ] Disable debug mode
- [ ] Add input validation and sanitization
- [ ] Implement rate limiting
- [ ] Add security headers
- [ ] Enable comprehensive logging
- [ ] Regular security updates
- [ ] Use firewall (ufw/iptables)
- [ ] Run as non-root user
- [ ] Regular backups
- [ ] Security audit

## Private Network Deployment

For use only on private home networks (recommended current usage):

### Network Configuration
```bash
# Firewall - allow only from local network
sudo ufw allow from 192.168.1.0/24 to any port 5000
sudo ufw allow from 192.168.1.0/24 to any port 3000
```

### Router Configuration
- Don't forward ports 5000 or 3000 to the internet
- Use strong WiFi password (WPA3 if available)
- Enable MAC address filtering (optional)
- Keep router firmware updated

## Reporting Security Issues

If you discover a security vulnerability, please:
1. **Do not** open a public issue
2. Email the repository owner with details
3. Allow time for a fix before public disclosure

## Dependencies Security

```bash
# Regularly check for vulnerable dependencies

# Python
pip install safety
safety check -r backend/requirements.txt

# Node.js
cd frontend
npm audit
npm audit fix
```

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/2.3.x/security/)
- [React Security Best Practices](https://owasp.org/www-project-web-security-testing-guide/)
- [Raspberry Pi Security](https://www.raspberrypi.com/documentation/computers/configuration.html#securing-your-raspberry-pi)

## License

This security document is part of the Media Player project and follows the same license.