import { useEffect, useMemo, useState } from 'react';
import './PageMenu.css';

export type PageMenuItem<K extends string> = {
  key: K;
  label: string;
};

export type PageMenuProps<K extends string> = {
  items: Array<PageMenuItem<K>>;
  activeKey: K;
  onSelect: (key: K) => void;
  storageKey: string;
  ariaLabel: string;
};

const MOBILE_MEDIA_QUERY = '(max-width: 768px)';

const getIsMobile = () => {
  try {
    return window.matchMedia(MOBILE_MEDIA_QUERY).matches;
  } catch {
    return false;
  }
};

function PageMenu<K extends string>({ items, activeKey, onSelect, storageKey, ariaLabel }: PageMenuProps<K>) {
  const activeLabel = useMemo(() => items.find(i => i.key === activeKey)?.label ?? 'Menu', [activeKey, items]);

  const [isMobile, setIsMobile] = useState(getIsMobile());
  const [isOpen, setIsOpen] = useState<boolean>(() => {
    const stored = window.localStorage.getItem(storageKey);
    if (stored === 'open') return true;
    if (stored === 'closed') return false;
    // Default collapsed unless a previous preference exists.
    return false;
  });

  useEffect(() => {
    const mql = window.matchMedia(MOBILE_MEDIA_QUERY);
    const onChange = () => setIsMobile(mql.matches);
    onChange();

    const anyMql = mql as unknown as {
      addEventListener?: (type: 'change', listener: () => void) => void;
      removeEventListener?: (type: 'change', listener: () => void) => void;
      addListener?: (listener: () => void) => void;
      removeListener?: (listener: () => void) => void;
    };

    if (typeof anyMql.addEventListener === 'function' && typeof anyMql.removeEventListener === 'function') {
      anyMql.addEventListener('change', onChange);
      return () => anyMql.removeEventListener?.('change', onChange);
    }

    // Legacy Safari fallback
    if (typeof anyMql.addListener === 'function' && typeof anyMql.removeListener === 'function') {
      anyMql.addListener(onChange);
      return () => anyMql.removeListener?.(onChange);
    }

    return undefined;
  }, []);

  useEffect(() => {
    window.localStorage.setItem(storageKey, isOpen ? 'open' : 'closed');
  }, [isOpen, storageKey]);

  useEffect(() => {
    if (!isMobile || !isOpen) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setIsOpen(false);
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [isMobile, isOpen]);

  const select = (key: K) => {
    onSelect(key);
    if (isMobile) setIsOpen(false);
  };

  return (
    <div className="page-menu">
      <div className="page-menu-bar">
        <button
          type="button"
          className="page-menu-toggle"
          onClick={() => setIsOpen(prev => !prev)}
          aria-expanded={isOpen}
          aria-label={isOpen ? 'Close menu' : 'Open menu'}
        >
          <span className="material-icons">menu</span>
          <span className="page-menu-toggle-label">{activeLabel}</span>
          <span className="page-menu-toggle-spacer" />
          <span className="material-icons">{isOpen ? 'expand_less' : 'expand_more'}</span>
        </button>
      </div>

      {isMobile ? (
        isOpen ? (
          <div
            className="page-menu-mobile-overlay"
            role="presentation"
            onMouseDown={(e) => {
              if (e.target === e.currentTarget) setIsOpen(false);
            }}
          >
            <div className="page-menu-mobile-drawer" role="presentation">
              <nav className="page-menu-list" aria-label={ariaLabel}>
                {items.map((item) => (
                  <button
                    key={item.key}
                    type="button"
                    className={`page-menu-item ${item.key === activeKey ? 'active' : ''}`}
                    onClick={() => select(item.key)}
                  >
                    {item.label}
                  </button>
                ))}
              </nav>
            </div>
          </div>
        ) : null
      ) : (
        <nav className={`tabs page-menu-tabs ${isOpen ? '' : 'page-menu-tabs-collapsed'}`} aria-label={ariaLabel}>
          {isOpen &&
            items.map((item) => (
              <button
                key={item.key}
                type="button"
                className={item.key === activeKey ? 'active' : ''}
                onClick={() => select(item.key)}
              >
                {item.label}
              </button>
            ))}
        </nav>
      )}
    </div>
  );
}

export default PageMenu;
