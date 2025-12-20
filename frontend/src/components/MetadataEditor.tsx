import { useState, useEffect } from 'react';
import './MetadataEditor.css';

const API_BASE_URL = '';

interface Metadata {
  title: string | null;
  artist: string | null;
  album: string | null;
  year: string | null;
  track_number: string | null;
  duration: number | null;
  custom_tags: { [key: string]: string };
}

interface MetadataEditorProps {
  trackPath: string;
  onClose: () => void;
}

const MetadataEditor = ({ trackPath, onClose }: MetadataEditorProps) => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editedMetadata, setEditedMetadata] = useState<Metadata | null>(null);
  const [newTagKey, setNewTagKey] = useState('');
  const [newTagValue, setNewTagValue] = useState('');

  const loadMetadata = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`${API_BASE_URL}/api/metadata`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ track_path: trackPath })
      });

      if (!response.ok) {
        throw new Error('Failed to load metadata');
      }

      const data = await response.json();
      setEditedMetadata(JSON.parse(JSON.stringify(data))); // Deep copy
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load metadata');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMetadata();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [trackPath]);

  const handleSave = async () => {
    if (!editedMetadata) return;

    try {
      setSaving(true);
      setError(null);
      
      const response = await fetch(`${API_BASE_URL}/api/metadata`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          track_path: trackPath,
          metadata: editedMetadata
        })
      });

      if (!response.ok) {
        throw new Error('Failed to save metadata');
      }

      const updatedData = await response.json();
      setEditedMetadata(JSON.parse(JSON.stringify(updatedData)));
      alert('Metadata saved successfully!');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save metadata');
    } finally {
      setSaving(false);
    }
  };

  const handleAddCustomTag = () => {
    if (!newTagKey || !newTagValue || !editedMetadata) return;

    const updatedMetadata = { ...editedMetadata };
    updatedMetadata.custom_tags = {
      ...updatedMetadata.custom_tags,
      [newTagKey]: newTagValue
    };

    setEditedMetadata(updatedMetadata);
    setNewTagKey('');
    setNewTagValue('');
  };

  const handleDeleteCustomTag = async (tagKey: string) => {
    if (!confirm(`Delete custom tag "${tagKey}"?`)) return;

    try {
      setSaving(true);
      setError(null);
      
      const response = await fetch(`${API_BASE_URL}/api/metadata/custom-tag`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          track_path: trackPath,
          tag_key: tagKey
        })
      });

      if (!response.ok) {
        throw new Error('Failed to delete custom tag');
      }

      const updatedData = await response.json();
      setEditedMetadata(JSON.parse(JSON.stringify(updatedData)));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete custom tag');
    } finally {
      setSaving(false);
    }
  };

  const handleFieldChange = (field: keyof Metadata, value: string) => {
    if (!editedMetadata) return;
    
    setEditedMetadata({
      ...editedMetadata,
      [field]: value || null
    });
  };

  if (loading) {
    return (
      <div className="metadata-editor-overlay">
        <div className="metadata-editor card">
          <div className="loading">Loading metadata...</div>
        </div>
      </div>
    );
  }

  if (!editedMetadata) {
    return (
      <div className="metadata-editor-overlay">
        <div className="metadata-editor card">
          <div className="error">Failed to load metadata</div>
          <button onClick={onClose} className="btn btn-secondary">Close</button>
        </div>
      </div>
    );
  }

  return (
    <div className="metadata-editor-overlay" onClick={onClose}>
      <div className="metadata-editor card" onClick={(e) => e.stopPropagation()}>
        <div className="editor-header">
          <h2>Edit Metadata</h2>
          <button onClick={onClose} className="close-btn">✕</button>
        </div>

        <div className="track-path-display">
          <strong>File:</strong> {trackPath}
        </div>

        {error && <div className="error-message">{error}</div>}

        <div className="editor-content">
          <section className="standard-fields">
            <h3>Standard Fields</h3>
            
            <div className="form-group">
              <label>Title</label>
              <input
                type="text"
                value={editedMetadata.title || ''}
                onChange={(e) => handleFieldChange('title', e.target.value)}
                placeholder="Song title"
              />
            </div>

            <div className="form-group">
              <label>Artist</label>
              <input
                type="text"
                value={editedMetadata.artist || ''}
                onChange={(e) => handleFieldChange('artist', e.target.value)}
                placeholder="Artist name"
              />
            </div>

            <div className="form-group">
              <label>Album</label>
              <input
                type="text"
                value={editedMetadata.album || ''}
                onChange={(e) => handleFieldChange('album', e.target.value)}
                placeholder="Album name"
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Year</label>
                <input
                  type="text"
                  value={editedMetadata.year || ''}
                  onChange={(e) => handleFieldChange('year', e.target.value)}
                  placeholder="2024"
                />
              </div>

              <div className="form-group">
                <label>Track Number</label>
                <input
                  type="text"
                  value={editedMetadata.track_number || ''}
                  onChange={(e) => handleFieldChange('track_number', e.target.value)}
                  placeholder="1"
                />
              </div>
            </div>

            {editedMetadata.duration && (
              <div className="info-field">
                <strong>Duration:</strong> {Math.floor(editedMetadata.duration / 60)}:{Math.floor(editedMetadata.duration % 60).toString().padStart(2, '0')}
              </div>
            )}
          </section>

          <section className="custom-tags-section">
            <h3>Custom Tags</h3>
            
            {Object.keys(editedMetadata.custom_tags).length === 0 ? (
              <p className="empty-message">No custom tags yet</p>
            ) : (
              <div className="tags-list">
                {Object.entries(editedMetadata.custom_tags).map(([key, value]) => (
                  <div key={key} className="tag-item">
                    <div className="tag-info">
                      <span className="tag-key">{key}</span>
                      <span className="tag-value">{value}</span>
                    </div>
                    <button
                      onClick={() => handleDeleteCustomTag(key)}
                      className="btn-delete"
                      disabled={saving}
                      title="Delete tag"
                    >
                      🗑️
                    </button>
                  </div>
                ))}
              </div>
            )}

            <div className="add-tag-form">
              <h4>Add Custom Tag</h4>
              <div className="form-row">
                <input
                  type="text"
                  value={newTagKey}
                  onChange={(e) => setNewTagKey(e.target.value)}
                  placeholder="Tag key (e.g., LAO:CUSTOM_KEY)"
                  className="tag-key-input"
                />
                <input
                  type="text"
                  value={newTagValue}
                  onChange={(e) => setNewTagValue(e.target.value)}
                  placeholder="Tag value"
                  className="tag-value-input"
                />
                <button
                  onClick={handleAddCustomTag}
                  className="btn btn-secondary"
                  disabled={!newTagKey || !newTagValue}
                >
                  Add
                </button>
              </div>
              <p className="hint">
                Tip: Use "LAO:" prefix for custom tags. Common examples: LAO:TAGS (for labels/genres), LAO:MUSIC_START, LAO:MUSIC_END, LAO:playcount, LAO:USERRATING, LAO:lastplayed
              </p>
            </div>
          </section>
        </div>

        <div className="editor-footer">
          <button onClick={onClose} className="btn btn-secondary" disabled={saving}>
            Cancel
          </button>
          <button onClick={handleSave} className="btn btn-primary" disabled={saving}>
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default MetadataEditor;
