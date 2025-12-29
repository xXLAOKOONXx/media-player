"""
User Manager
Handles user authentication and authorization
"""

import bcrypt
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify


class UserManager:
    """Manages user authentication and authorization"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        # Session expiry: 30 days
        self.session_expiry_days = 30
    
    def hash_password(self, password):
        """Hash a password using bcrypt"""
        if password is None or password == '':
            return None
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password, password_hash):
        """Verify a password against a hash"""
        if password_hash is None:
            # User has no password set - any password is invalid
            return password is None or password == ''
        if password is None or password == '':
            return False
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def authenticate(self, username, password=None):
        """Authenticate a user with username and password"""
        user = self.db.get_user_by_username(username)
        
        if not user:
            return None
        
        # Check password
        if user['password_hash'] is None:
            # No password required for this user
            if password is None or password == '':
                return user
            else:
                # User has no password but one was provided
                return None
        else:
            # Password required
            if self.verify_password(password, user['password_hash']):
                return user
            else:
                return None
    
    def create_session(self, user_id):
        """Create a new session for a user"""
        session_id = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(days=self.session_expiry_days)
        
        self.db.create_session(session_id, user_id, expires_at.timestamp())
        
        return session_id
    
    def get_user_from_session(self, session_id):
        """Get user from session ID"""
        if not session_id:
            return None
        
        session = self.db.get_session(session_id)
        
        if not session:
            return None
        
        # Check if session is expired
        if session['expires_at'] < datetime.now().timestamp():
            self.db.delete_session(session_id)
            return None
        
        user = self.db.get_user_by_id(session['user_id'])
        return user
    
    def logout(self, session_id):
        """Logout a user by deleting their session"""
        if session_id:
            self.db.delete_session(session_id)
    
    def create_user(self, username, password, role):
        """Create a new user"""
        # Hash password if provided
        password_hash = self.hash_password(password) if password else None
        
        user_id = self.db.create_user(username, password_hash, role)
        return user_id
    
    def update_password(self, user_id, new_password):
        """Update a user's password"""
        password_hash = self.hash_password(new_password) if new_password else None
        self.db.update_user_password(user_id, password_hash)
    
    def delete_user(self, user_id):
        """Delete a user"""
        self.db.delete_user(user_id)
    
    def get_all_users(self):
        """Get all users (without password hashes)"""
        return self.db.get_all_users()
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        self.db.cleanup_expired_sessions()


def require_auth(user_manager):
    """Decorator to require authentication"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get session from cookie
            session_id = request.cookies.get('session_id')
            
            user = user_manager.get_user_from_session(session_id)
            
            if not user:
                return jsonify({'error': 'Authentication required'}), 401
            
            # Add user to request context
            request.current_user = user
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def require_admin(user_manager):
    """Decorator to require admin role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get session from cookie
            session_id = request.cookies.get('session_id')
            
            user = user_manager.get_user_from_session(session_id)
            
            if not user:
                return jsonify({'error': 'Authentication required'}), 401
            
            if user['role'] != 'admin':
                return jsonify({'error': 'Admin access required'}), 403
            
            # Add user to request context
            request.current_user = user
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator
