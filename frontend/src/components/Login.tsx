import { useState, useEffect } from 'react';
import './Login.css';

const API_BASE_URL = '';

interface User {
  id: number;
  username: string;
  role: string;
}

interface LoginProps {
  onLoginSuccess: (user: User) => void;
}

function Login({ onLoginSuccess }: LoginProps) {
  const [users, setUsers] = useState<User[]>([]);
  const [selectedUser, setSelectedUser] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loadingUsers, setLoadingUsers] = useState(true);

  useEffect(() => {
    // Fetch available users (without sensitive info)
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/users`);
      if (response.ok) {
        const data = await response.json();
        setUsers(data);
      } else if (response.status === 401 || response.status === 403) {
        // If we can't access users list, provide default options
        setUsers([
          { id: 1, username: 'admin', role: 'admin' },
          { id: 2, username: 'default', role: 'default' }
        ]);
      }
    } catch (err) {
      console.error('Error fetching users:', err);
      // Provide default options on error
      setUsers([
        { id: 1, username: 'admin', role: 'admin' },
        { id: 2, username: 'default', role: 'default' }
      ]);
    } finally {
      setLoadingUsers(false);
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedUser) {
      setError('Please select a user');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: selectedUser,
          password: password || ''
        }),
        credentials: 'include' // Important for cookies
      });

      if (response.ok) {
        const user = await response.json();
        onLoginSuccess(user);
      } else {
        const data = await response.json();
        setError(data.error || 'Login failed');
      }
    } catch (err) {
      console.error('Login error:', err);
      setError('Failed to connect to server');
    } finally {
      setLoading(false);
    }
  };

  const selectedUserObj = users.find(u => u.username === selectedUser);
  const needsPassword = selectedUserObj?.role === 'admin' && password === '';

  return (
    <div className="login-container">
      <div className="login-box">
        <h1><span className="material-icons">music_note</span>Media Player</h1>
        <h2>Login</h2>
        
        {loadingUsers ? (
          <p>Loading...</p>
        ) : (
          <form onSubmit={handleLogin}>
            <div className="form-group">
              <label htmlFor="user-select">Select User:</label>
              <select
                id="user-select"
                value={selectedUser}
                onChange={(e) => setSelectedUser(e.target.value)}
                disabled={loading}
              >
                <option value="">-- Select a user --</option>
                {users.map(user => (
                  <option key={user.id} value={user.username}>
                    {user.username} ({user.role})
                  </option>
                ))}
              </select>
            </div>

            {selectedUser && selectedUserObj?.role === 'admin' && (
              <div className="form-group">
                <label htmlFor="password">Password (optional for admin):</label>
                <input
                  type="password"
                  id="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={loading}
                  placeholder="Leave empty if no password is set"
                />
              </div>
            )}

            {error && <div className="error-message">{error}</div>}

            <button
              type="submit"
              disabled={loading || !selectedUser}
              className="login-button"
            >
              {loading ? 'Logging in...' : 'Login'}
            </button>
          </form>
        )}

        <p className="info-text">
          Default user has restricted access. Admin can manage settings and users.
        </p>
      </div>
    </div>
  );
}

export default Login;
