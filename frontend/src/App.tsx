import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import './App.css';
import AudioPage from './pages/AudioPage';
import VideoPage from './pages/VideoPage';

function Navigation() {
  const location = useLocation();
  
  return (
    <header className="App-header">
      <h1><span className="material-icons">music_note</span>Media Player</h1>
      <nav className="main-nav">
        <Link 
          to="/audio" 
          className={location.pathname === '/audio' || location.pathname === '/' ? 'active' : ''}
        >
          <span className="material-icons">audiotrack</span>
          Audio
        </Link>
        <Link 
          to="/video" 
          className={location.pathname === '/video' ? 'active' : ''}
        >
          <span className="material-icons">video_library</span>
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
        <Navigation />
        <main className="App-main">
          <Routes>
            <Route path="/" element={<AudioPage />} />
            <Route path="/audio" element={<AudioPage />} />
            <Route path="/video" element={<VideoPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
