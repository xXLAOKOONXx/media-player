import { useState } from 'react';
import './FolderBrowser.css';

const API_BASE_URL = '';

interface BrowseItem {
  name: string;
  path: string;
  is_directory: boolean;
}

interface FolderBrowserProps {
  initialPath?: string;
  onSelectFolder: (path: string) => void;
  onCancel: () => void;
  currentValue?: string;
}

const FolderBrowser = ({ initialPath = '/', onSelectFolder, onCancel, currentValue }: FolderBrowserProps) => {
  const [browsePath, setBrowsePath] = useState(initialPath);
  const [browseItems, setBrowseItems] = useState<BrowseItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const browsePath_fn = async (path: string) => {
    try {
      setIsLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/browse`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path })
      });
      const data = await response.json();
      setBrowseItems(data.items || []);
      setBrowsePath(data.current_path || path);
    } catch (err) {
      console.error('Error browsing path:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStartBrowse = () => {
    browsePath_fn(currentValue || browsePath);
  };

  const handleSelectCurrent = () => {
    onSelectFolder(browsePath);
  };

  return (
    <div className="folder-browser">
      <div className="folder-browser-controls">
        <input
          type="text"
          value={currentValue || ''}
          readOnly
          placeholder="No path selected"
          className="folder-path-display"
        />
        <button
          type="button"
          onClick={handleStartBrowse}
          className="browse-button"
        >
          <span className="material-icons">folder_open</span>
          Browse
        </button>
      </div>

      {browseItems.length > 0 && (
        <div className="browse-results">
          <h4>Current Path: {browsePath}</h4>
          {isLoading ? (
            <div className="loading">Loading...</div>
          ) : (
            <>
              <ul className="browse-items">
                <li
                  className="browse-item"
                  onClick={() => browsePath_fn(browsePath + '/..')}
                >
                  <span className="material-icons">folder</span>
                  <span className="item-name">..</span>
                </li>
                {browseItems
                  .filter(item => item.is_directory)
                  .map((item, idx) => (
                    <li
                      key={idx}
                      className="browse-item"
                      onClick={() => browsePath_fn(item.path)}
                    >
                      <span className="material-icons">folder</span>
                      <span className="item-name">{item.name}</span>
                    </li>
                  ))}
              </ul>
              <div className="browse-actions">
                <button
                  type="button"
                  onClick={handleSelectCurrent}
                  className="select-button"
                >
                  <span className="material-icons">check</span>
                  Select Current Folder
                </button>
                <button
                  type="button"
                  onClick={onCancel}
                  className="cancel-button"
                >
                  <span className="material-icons">close</span>
                  Cancel
                </button>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default FolderBrowser;
