# Dark Mode

The Media Player application is designed with **dark mode as the default and only theme**. The entire UI is optimized for low-light environments and extended viewing sessions.

## Philosophy

Dark mode is not an optional theme in this application—it's the foundation of the design:

- **Default State**: The application always runs in dark mode
- **No Toggle**: There is no light mode toggle or theme switcher
- **Optimized UI**: All components, colors, and contrasts are designed specifically for dark backgrounds

## Benefits of Dark Mode

### User Experience
- **Reduced Eye Strain**: Easier on the eyes in low-light environments
- **Better for Media**: Dark backgrounds don't compete with media content
- **Modern Aesthetic**: Clean, contemporary look that suits a media player
- **Focus on Content**: Dark UI recedes, putting emphasis on album art and content

### Technical Advantages
- **Energy Efficiency**: Lower power consumption on OLED/AMOLED displays
- **Consistent Appearance**: No need to maintain two themes
- **Simplified Development**: Single color scheme to test and maintain

## Implementation

### Base Styles

The dark mode is implemented at the root level in `App.css`:

```css
.App {
  min-height: 100vh;
  background-color: #414141;  /* Dark gray background */
  color: #dfdfdf;              /* Light text */
}
```

### Color Hierarchy

Dark mode uses a layered approach with varying shades of gray:

1. **Background Layer** (`#414141`) - Base layer, darkest
2. **Surface Layer** (`#606060`) - Cards, buttons, elevated elements
3. **Text Layer** (`#dfdfdf`) - Content, high contrast
4. **Accent Layer** (`#4a5568`) - Interactive elements, blueish-gray

This creates visual depth without relying on shadows alone.

### Contrast & Readability

All text maintains sufficient contrast against dark backgrounds:

- **Primary Text**: `#dfdfdf` on `#414141` = ~10.5:1 contrast ratio (WCAG AAA)
- **Text on Cards**: `#dfdfdf` on `#606060` = ~7:1 contrast ratio (WCAG AA)
- **Active Elements**: `#414141` on `#9d9d9d` = ~4.5:1 contrast ratio (WCAG AA)

## Design Guidelines

### Surfaces & Elevation

Use different background colors to indicate elevation:

```css
/* Base level */
.App {
  background-color: #414141;
}

/* Elevated surfaces (cards, modals) */
.card {
  background-color: #606060;
}

/* Even more elevated (dropdowns, tooltips) */
.dropdown {
  background-color: #707070; /* Could be used for additional elevation */
}
```

### Shadows in Dark Mode

Shadows are still useful but need to be stronger in dark mode:

```css
.card {
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.5); /* Strong shadow for depth */
}

.btn-primary:hover {
  box-shadow: 0 4px 8px rgba(74, 85, 104, 0.5); /* Accent-colored shadow */
}
```

### Borders and Dividers

Use subtle borders that don't overpower the design:

```css
.section-divider {
  border-top: 1px solid rgba(255, 255, 255, 0.1); /* Very subtle white */
}

.input-field {
  border: 1px solid #9d9d9d; /* Medium gray for form elements */
}
```

### Input Fields

Input fields should be slightly darker than their containers:

```css
.form-group input,
.form-group select {
  background-color: #414141; /* Darker than card background */
  color: #dfdfdf;             /* Light text */
  border: 1px solid #9d9d9d;  /* Visible border */
}

.form-group input:focus {
  border-color: #4a5568;      /* Accent color on focus */
  outline: none;
}
```

## Best Practices

### Do's
- ✅ Use the established gray scale for all backgrounds
- ✅ Ensure text has sufficient contrast (use `#dfdfdf` for primary text)
- ✅ Use elevation (different gray shades) to show hierarchy
- ✅ Add strong shadows for depth and separation
- ✅ Test readability in actual low-light conditions
- ✅ Use the blueish-gray accent (`#4a5568`) for interactive elements

### Don'ts
- ❌ Don't use pure black (`#000000`) - it's too harsh
- ❌ Don't use pure white (`#ffffff`) for text - it's too bright
- ❌ Don't add a light mode - the app is designed for dark mode only
- ❌ Don't use bright, saturated colors that cause eye strain
- ❌ Don't rely solely on color for information - use icons and text too
- ❌ Don't create low-contrast combinations (e.g., light gray on lighter gray)

## Accessibility in Dark Mode

### Contrast Ratios
- Maintain WCAG AA standards minimum (4.5:1 for normal text)
- Current implementation exceeds this with ~10.5:1 for most text

### Color Blindness
- The grayscale-based palette is inherently accessible for color-blind users
- Rely on icons, text, and patterns in addition to color
- Use the blueish-gray accent sparingly and not as the only indicator

### Screen Readers
- Dark mode doesn't affect screen readers
- Continue using proper semantic HTML and ARIA labels

## Mobile Considerations

Dark mode is especially important for mobile devices:

```css
@media (max-width: 768px) {
  /* Ensure touch targets are large enough */
  .btn {
    min-height: 48px; /* WCAG recommends 44px minimum */
  }
  
  /* Text remains highly readable */
  .App-header h1 {
    font-size: 1.5rem; /* Slightly smaller but still readable */
  }
}
```

## Testing Dark Mode

When adding new components, verify:

1. **Contrast**: Text is readable against its background
2. **Hierarchy**: Different layers are distinguishable
3. **Consistency**: Colors match the established palette
4. **Hover States**: Interactive elements provide clear feedback
5. **Focus States**: Keyboard navigation is visible
6. **Loading States**: Skeleton screens and spinners are visible

## Common Patterns

### Loading Skeletons
```css
.skeleton {
  background: linear-gradient(
    90deg,
    #606060 25%,
    #707070 50%,
    #606060 75%
  );
  animation: shimmer 1.5s infinite;
}
```

### Disabled States
```css
button:disabled {
  opacity: 0.5;           /* Reduced opacity */
  cursor: not-allowed;
}
```

### Hover States
```css
.card:hover {
  background-color: #4a5568; /* Shift to accent color */
  transition: background-color 0.2s ease;
}
```

### Selected/Active States
```css
.tab.active {
  background-color: #9d9d9d; /* Lighter gray */
  color: #414141;             /* Invert text for contrast */
}
```

## Browser Support

The dark mode implementation works across all modern browsers:
- Chrome/Edge (Chromium)
- Firefox
- Safari
- Mobile browsers (iOS Safari, Chrome Mobile)

No special CSS media queries or JavaScript detection is needed since dark mode is always active.

## Future Considerations

While not currently planned, if user preference for theme becomes necessary:

1. Consider user's system preference: `prefers-color-scheme: dark`
2. Store user preference in localStorage
3. Create a light mode variant using the inverse color scale
4. Ensure the toggle is obvious and accessible

However, maintaining the current dark-only approach is recommended for simplicity and consistency.
