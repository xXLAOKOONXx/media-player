import { useState, useEffect } from 'react';
import type { User } from '../types';
import './UserManagement.css';

const API_BASE_URL = '';

interface UserManagementProps {
  currentUser: User | null;
}

function UserManagement({ currentUser }: UserManagementProps) {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showPasswordForm, setShowPasswordForm] = useState(false);
  const [newUsername, setNewUsername] = useState('');
  const [newUserPassword, setNewUserPassword] = useState('');
  const [adminPassword, setAdminPassword] = useState('');
  const [creatingUser, setCreatingUser] = useState(false);
  const [updatingPassword, setUpdatingPassword] = useState(false);

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/users`, {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        setUsers(data);
        setError(null);
      } else {
        setError('Failed to fetch users');
      }
    } catch (err) {
      console.error('Error fetching users:', err);
      setError('Failed to connect to server');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!newUsername.trim()) {
      alert('Please enter a username');
      return;
    }

    setCreatingUser(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/users`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          username: newUsername.trim(),
          password: newUserPassword || null,
          role: 'custom'
        })
      });

      if (response.ok) {
        alert('User created successfully');
        setNewUsername('');
        setNewUserPassword('');
        setShowCreateForm(false);
        fetchUsers();
      } else {
        const data = await response.json();
        alert(`Error: ${data.error || 'Failed to create user'}`);
      }
    } catch (err) {
      console.error('Error creating user:', err);
      alert('Failed to connect to server');
    } finally {
      setCreatingUser(false);
    }
  };

  const handleDeleteUser = async (userId: number, username: string) => {
    if (!confirm(`Are you sure you want to delete user "${username}"?`)) {
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/users/${userId}`, {
        method: 'DELETE',
        credentials: 'include'
      });

      if (response.ok) {
        alert('User deleted successfully');
        fetchUsers();
      } else {
        const data = await response.json();
        alert(`Error: ${data.error || 'Failed to delete user'}`);
      }
    } catch (err) {
      console.error('Error deleting user:', err);
      alert('Failed to connect to server');
    }
  };

  const handleUpdateAdminPassword = async (e: React.FormEvent) => {
    e.preventDefault();

    setUpdatingPassword(true);

    const adminUser = users.find(u => u.username === 'admin');
    if (!adminUser) {
      alert('Admin user not found');
      setUpdatingPassword(false);
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/users/${adminUser.id}/password`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          password: adminPassword || null
        })
      });

      if (response.ok) {
        alert('Admin password updated successfully');
        setAdminPassword('');
        setShowPasswordForm(false);
      } else {
        const data = await response.json();
        alert(`Error: ${data.error || 'Failed to update password'}`);
      }
    } catch (err) {
      console.error('Error updating password:', err);
      alert('Failed to connect to server');
    } finally {
      setUpdatingPassword(false);
    }
  };

  if (currentUser?.role !== 'admin') {
    return (
      <div className="user-management">
        <p>You do not have permission to manage users.</p>
      </div>
    );
  }

  if (loading) {
    return <div className="user-management"><p>Loading users...</p></div>;
  }

  if (error) {
    return <div className="user-management"><p className="error">{error}</p></div>;
  }

  return (
    <div className="user-management">
      <h2>User Management</h2>

      <div className="section">
        <h3>Existing Users</h3>
        <table className="users-table">
          <thead>
            <tr>
              <th>Username</th>
              <th>Role</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map(user => (
              <tr key={user.id}>
                <td>{user.username}</td>
                <td>{user.role}</td>
                <td>
                  {user.role === 'custom' && (
                    <button
                      onClick={() => handleDeleteUser(user.id, user.username)}
                      className="delete-button"
                      title="Delete user"
                    >
                      <span className="material-icons">delete</span>
                    </button>
                  )}
                  {user.role !== 'custom' && (
                    <span className="system-user">System User</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="section">
        <h3>Create New User</h3>
        {!showCreateForm ? (
          <button 
            onClick={() => setShowCreateForm(true)} 
            className="action-button"
            title="Create new user"
          >
            <span className="material-icons">add</span>
          </button>
        ) : (
          <form onSubmit={handleCreateUser} className="user-form">
            <div className="form-group">
              <label>Username:</label>
              <input
                type="text"
                value={newUsername}
                onChange={(e) => setNewUsername(e.target.value)}
                disabled={creatingUser}
                required
              />
            </div>
            <div className="form-group">
              <label>Password (optional):</label>
              <input
                type="password"
                value={newUserPassword}
                onChange={(e) => setNewUserPassword(e.target.value)}
                disabled={creatingUser}
                placeholder="Leave empty for no password"
              />
            </div>
            <div className="form-actions">
              <button 
                type="submit" 
                disabled={creatingUser} 
                className="action-button"
                title="Create user"
              >
                <span className="material-icons">{creatingUser ? 'hourglass_empty' : 'check'}</span>
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowCreateForm(false);
                  setNewUsername('');
                  setNewUserPassword('');
                }}
                disabled={creatingUser}
                className="cancel-button"
                title="Cancel"
              >
                <span className="material-icons">close</span>
              </button>
            </div>
          </form>
        )}
      </div>

      <div className="section">
        <h3>Admin Password</h3>
        {!showPasswordForm ? (
          <button 
            onClick={() => setShowPasswordForm(true)} 
            className="action-button"
            title="Change admin password"
          >
            <span className="material-icons">vpn_key</span>
          </button>
        ) : (
          <form onSubmit={handleUpdateAdminPassword} className="user-form">
            <div className="form-group">
              <label>New Admin Password:</label>
              <input
                type="password"
                value={adminPassword}
                onChange={(e) => setAdminPassword(e.target.value)}
                disabled={updatingPassword}
                placeholder="Leave empty to remove password"
              />
            </div>
            <div className="form-actions">
              <button 
                type="submit" 
                disabled={updatingPassword} 
                className="action-button"
                title="Update password"
              >
                <span className="material-icons">{updatingPassword ? 'hourglass_empty' : 'check'}</span>
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowPasswordForm(false);
                  setAdminPassword('');
                }}
                disabled={updatingPassword}
                className="cancel-button"
                title="Cancel"
              >
                <span className="material-icons">close</span>
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

export default UserManagement;
