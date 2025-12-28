# Icon Usage Guidelines

The Media Player uses Material Icons as the primary icon library, prioritizing visual communication through icons over text labels.

## Icon Library

### Material Icons
- **Package**: `material-icons` (npm package)
- **Import**: Icons are loaded globally via `material-icons/iconfont/material-icons.css`
- **Documentation**: [Material Icons Official](https://fonts.google.com/icons)

## Implementation

### Basic Usage

Icons are implemented using a `<span>` element with the `material-icons` class:

```tsx
<span className="material-icons">icon_name</span>
```

### Common Icon Names Used in the Application

#### Media Playback
- `play_arrow` - Play button
- `pause` - Pause button
- `skip_next` - Next track
- `skip_previous` - Previous track
- `stop` - Stop playback
- `volume_up` - Volume control
- `volume_down` - Volume decrease
- `volume_off` - Mute

#### Navigation & UI
- `folder` - Folder/directory representation
- `folder_special` - Special folder (e.g., playlists)
- `playlist_add` - Add to playlist
- `queue_music` - Queue/playlist view
- `search` - Search functionality
- `add` - Add/create action
- `delete` - Delete action
- `edit` - Edit action
- `build` - Under construction/settings

#### Status & Information
- `check` - Confirmation/success
- `error` - Error state
- `info` - Information
- `warning` - Warning state

## Design Principles

### Icon Over Text
When designing UI elements, prefer icons over text labels:

✅ **Preferred**:
```tsx
<button>
  <span className="material-icons">add</span>
</button>
```

❌ **Avoid when icon is clear**:
```tsx
<button>Add New Item</button>
```

⚠️ **Exception**: Use both icon and text for:
- Actions that may not be immediately clear from the icon alone
- Important actions where clarity is critical
- Primary CTAs (Call-to-Action buttons)

### Accessibility

Always consider accessibility when using icon-only buttons:

```tsx
// Use aria-label for screen readers
<button aria-label="Add new item">
  <span className="material-icons">add</span>
</button>

// Or use title attribute for tooltips
<button title="Add new item">
  <span className="material-icons">add</span>
</button>
```

## Styling Icons

### Size
Icons inherit font size from their parent element:

```css
/* Default size */
.material-icons {
  font-size: 24px; /* Default Material Icons size */
}

/* Larger icons */
.material-icons.large {
  font-size: 48px;
}

/* Smaller icons */
.material-icons.small {
  font-size: 18px;
}
```

### Color
Icons inherit the text color:

```css
/* Icons will be light gray like other text */
.some-container {
  color: #dfdfdf;
}

.some-container .material-icons {
  /* Inherits #dfdfdf from parent */
}
```

### Alignment
Material Icons are designed to align with text:

```css
.material-icons {
  vertical-align: middle; /* Aligns with text baseline */
}
```

### Spacing
When combining icons with text:

```css
/* Icon before text */
.icon-label .material-icons {
  margin-right: 0.5rem;
}

/* Icon after text */
.label-icon .material-icons {
  margin-left: 0.5rem;
}
```

## Usage Examples from Codebase

### Header with Icon
```tsx
<h1>
  <span className="material-icons">headphones</span>
  Media Player
</h1>
```

### Button with Icon Only
```tsx
<button className="btn-primary" onClick={handleAdd}>
  <span className="material-icons">add</span>
</button>
```

### List Item with Icon
```tsx
<div className="list-item">
  <span className="material-icons">folder</span>
  <span>Folder Name</span>
</div>
```

### Search Input with Icon
```tsx
<div className="search-container">
  <span className="material-icons">search</span>
  <input type="text" placeholder="Search..." />
</div>
```

## Best Practices

### Do's
- ✅ Use Material Icons for all icon needs
- ✅ Prefer icons for common actions (add, delete, edit, search, etc.)
- ✅ Use semantic icon names that match their function
- ✅ Provide aria-label or title for icon-only buttons
- ✅ Keep icon usage consistent throughout the app
- ✅ Use `vertical-align: middle` for inline icons with text

### Don'ts
- ❌ Don't mix icon libraries (stick to Material Icons)
- ❌ Don't use obscure icons that users won't understand
- ❌ Don't use icons without accessibility attributes for interactive elements
- ❌ Don't override Material Icons default styles unnecessarily
- ❌ Don't use text labels when a well-known icon would suffice

## Finding Icons

When you need a new icon:

1. Visit [Google Fonts Icons](https://fonts.google.com/icons)
2. Search for the concept you want to represent
3. Click on an icon to see its name
4. Use the icon name in your code: `<span className="material-icons">icon_name</span>`

## Alternative Icon Variants

Material Icons supports different variants (not currently used in this app but available):

- **Filled** (default): `material-icons`
- **Outlined**: `material-icons-outlined`
- **Rounded**: `material-icons-round`
- **Sharp**: `material-icons-sharp`
- **Two-tone**: `material-icons-two-tone`

Currently, the application uses the default filled variant exclusively for consistency.

## Empty States with Icons

Icons are effective in empty states to provide visual context:

```tsx
<div className="empty-state">
  <span className="material-icons">folder_open</span>
  <p>No items found</p>
</div>
```

## Consistency Checklist

When adding new features, ensure:
- [ ] All action buttons use appropriate Material Icons
- [ ] Icon-only buttons have accessibility attributes
- [ ] Icons are used consistently with existing patterns
- [ ] New icons don't duplicate functionality of existing icons
- [ ] Icons align properly with adjacent text or elements
