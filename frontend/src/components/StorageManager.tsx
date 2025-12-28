import { useState, useEffect } from 'react';
import './StorageManager.css';

const API_BASE_URL = '';

interface Storage {
  id: number;
  name: string;
  type: string;
  host: string;
  share: string;
  username: string;
  mount_point: string;
}

const StorageManager = () => {
  const [storages, setStorages] = useState<Storage[]>([]);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newStorage, setNewStorage] = useState({
    name: '',
    type: 'smb',
    host: '',
    share: '',
    username: '',
    password: '',
    mount_point: ''
  });

  useEffect(() => {
    loadStorages();
  }, []);

  const loadStorages = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/audio/storage`);
      const data = await response.json();
      setStorages(data);
    } catch (err) {
      console.error('Error loading storages:', err);
    }
  };

  const handleAddStorage = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await fetch(`${API_BASE_URL}/api/audio/storage`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newStorage)
      });
      setNewStorage({
        name: '',
        type: 'smb',
        host: '',
        share: '',
        username: '',
        password: '',
        mount_point: ''
      });
      setShowAddForm(false);
      loadStorages();
    } catch (err) {
      console.error('Error adding storage:', err);
    }
  };

  const handleDeleteStorage = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this storage?')) {
      return;
    }
    
    try {
      await fetch(`${API_BASE_URL}/api/audio/storage/${id}`, {
        method: 'DELETE'
      });
      loadStorages();
    } catch (err) {
      console.error('Error deleting storage:', err);
    }
  };

  return (
    <div className="storage-manager card">
      <div className="header-row">
        <h2>Network Storage</h2>
        <button className="btn btn-primary" onClick={() => setShowAddForm(!showAddForm)}>
          {showAddForm ? 'Cancel' : '+ Add Storage'}
        </button>
      </div>

      <p className="description">
        Configure network storage locations (SMB/CIFS, NFS) to access your media files.
      </p>

      {showAddForm && (
        <form onSubmit={handleAddStorage} className="add-form">
          <div className="form-group">
            <label>Storage Name</label>
            <input
              type="text"
              value={newStorage.name}
              onChange={(e) => setNewStorage({ ...newStorage, name: e.target.value })}
              placeholder="My Network Storage"
              required
            />
          </div>

          <div className="form-group">
            <label>Type</label>
            <select
              value={newStorage.type}
              onChange={(e) => setNewStorage({ ...newStorage, type: e.target.value })}
            >
              <option value="smb">SMB/CIFS</option>
              <option value="nfs">NFS</option>
            </select>
          </div>

          <div className="form-group">
            <label>Host/Server</label>
            <input
              type="text"
              value={newStorage.host}
              onChange={(e) => setNewStorage({ ...newStorage, host: e.target.value })}
              placeholder="192.168.1.100 or server.local"
              required
            />
          </div>

          <div className="form-group">
            <label>Share Name</label>
            <input
              type="text"
              value={newStorage.share}
              onChange={(e) => setNewStorage({ ...newStorage, share: e.target.value })}
              placeholder="media"
              required
            />
          </div>

          <div className="form-group">
            <label>Username</label>
            <input
              type="text"
              value={newStorage.username}
              onChange={(e) => setNewStorage({ ...newStorage, username: e.target.value })}
              placeholder="guest or username"
            />
          </div>

          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              value={newStorage.password}
              onChange={(e) => setNewStorage({ ...newStorage, password: e.target.value })}
              placeholder="Optional"
            />
          </div>

          <div className="form-group">
            <label>Mount Point (optional)</label>
            <input
              type="text"
              value={newStorage.mount_point}
              onChange={(e) => setNewStorage({ ...newStorage, mount_point: e.target.value })}
              placeholder="/mnt/media_1"
            />
          </div>

          <button type="submit" className="btn btn-primary">Add Storage</button>
        </form>
      )}

      <div className="storages-list">
        {storages.length === 0 ? (
          <div className="empty-state">
            <p>No network storage configured</p>
            <p>Add a network storage location to access your media files</p>
          </div>
        ) : (
          storages.map((storage) => (
            <div key={storage.id} className="list-item storage-item">
              <div className="storage-info">
                <div className="storage-name">
                  <strong>{storage.name}</strong>
                  <span className="storage-type">{storage.type.toUpperCase()}</span>
                </div>
                <div className="storage-details">
                  <span>📍 //{storage.host}/{storage.share}</span>
                  <span>👤 {storage.username || 'guest'}</span>
                  <span>📂 {storage.mount_point}</span>
                </div>
              </div>
              <button
                className="btn btn-danger"
                onClick={() => handleDeleteStorage(storage.id)}
              >
                Delete
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default StorageManager;