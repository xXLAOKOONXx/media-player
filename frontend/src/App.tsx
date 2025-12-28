import { BrowserRouter as Router, Routes, Route, Navigate, useLocation, Link } from 'react-router-dom';
import './App.css';
import AudioPage from './pages/AudioPage';
import VideoPage from './pages/VideoPage';

function AppHeader() {
  const location = useLocation();
  const isAudioPath = location.pathname.startsWith('/audio');
  const isVideoPath = location.pathname.startsWith('/video');

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
    </header>
  );
}

function App() {
  return (
    <Router>
      <div className="App">
        <AppHeader />
        <Routes>
          {/* Redirect root to audio player */}
          <Route path="/" element={<Navigate to="/audio/player" replace />} />
          
          {/* Audio routes */}
          <Route path="/audio/*" element={<AudioPage />} />
          <Route path="/audio" element={<Navigate to="/audio/player" replace />} />
          
          {/* Video routes */}
          <Route path="/video/*" element={<VideoPage />} />
          <Route path="/video" element={<Navigate to="/video/player" replace />} />
          
          {/* Catch-all redirect to audio player */}
          <Route path="*" element={<Navigate to="/audio/player" replace />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
