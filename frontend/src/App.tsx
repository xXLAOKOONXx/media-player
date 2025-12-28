import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation, Link } from 'react-router-dom';
import type { User } from './types';
import './App.css';
import AudioPage from './pages/AudioPage';
import VideoPage from './pages/VideoPage';
import Login from './components/Login';

const API_BASE_URL = '';

interface AppHeaderProps {
  user: User | null;
  onLogout: () => void;
}

function AppHeader({ user, onLogout }: AppHeaderProps) {
  const location = useLocation();
  const isAudioPath = location.pathname.startsWith('/audio');
  const isVideoPath = location.pathname.startsWith('/video');
  const isLoginPath = location.pathname === '/login';

  // Don't show header on login page
  if (isLoginPath) {
    return null;
  }

  return (
    <header className="App-header">
      <h1><span className="material-icons">music_note</span>Media Player</h1>
      <nav className="main-nav">
        <Link 
          to="/audio/player" 
          className={isAudioPath ? 'active' : ''}
        >
          Audio
        </Link>
        <Link 
          to="/video" 
          className={isVideoPath ? 'active' : ''}
        >
          Video
        </Link>
      </nav>
      {user && (
        <div className="user-info">
          <span className="username">{user.username} ({user.role})</span>
          <button onClick={onLogout} className="logout-button">Logout</button>
        </div>
      )}
    </header>
  );
}

function App() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is already authenticated
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/current-user`, {
        credentials: 'include'
      });
      
      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
      }
    } catch (err) {
      console.error('Auth check failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleLoginSuccess = (userData: User) => {
    setUser(userData);
  };

  const handleLogout = async () => {
    try {
      await fetch(`${API_BASE_URL}/api/auth/logout`, {
        method: 'POST',
        credentials: 'include'
      });
    } catch (err) {
      console.error('Logout failed:', err);
    } finally {
      setUser(null);
    }
  };

  if (loading) {
    return (
      <div className="App">
        <div className="loading-screen">Loading...</div>
      </div>
    );
  }

  return (
    <Router>
      <div className="App">
        <AppHeader user={user} onLogout={handleLogout} />
        <Routes>
          {/* Login route */}
          <Route 
            path="/login" 
            element={user ? <Navigate to="/audio/player" replace /> : <Login onLoginSuccess={handleLoginSuccess} />} 
          />
          
          {/* Protected routes - redirect to login if not authenticated */}
          <Route 
            path="/" 
            element={user ? <Navigate to="/audio/player" replace /> : <Navigate to="/login" replace />} 
          />
          
          <Route 
            path="/audio/*" 
            element={user ? <AudioPage currentUser={user} /> : <Navigate to="/login" replace />} 
          />
          
          <Route 
            path="/video/*" 
            element={user ? <VideoPage currentUser={user} /> : <Navigate to="/login" replace />} 
          />
          
          {/* Catch-all redirect */}
          <Route 
            path="*" 
            element={user ? <Navigate to="/audio/player" replace /> : <Navigate to="/login" replace />} 
          />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
