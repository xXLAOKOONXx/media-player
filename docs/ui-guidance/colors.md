# Color Scheme

The Media Player uses a minimal, dark-themed color palette based on grayscale with blueish-gray accents.

## Color Palette

### Primary Colors

#### Background
- **Main Background**: `#414141`
  - Used for: Page background, input fields
  - Description: Dark gray that provides the base for the entire application

#### Surfaces
- **Card/Surface**: `#606060`
  - Used for: Cards, buttons, list items, navigation items
  - Description: Medium gray for elevated surfaces and interactive elements

#### Text
- **Primary Text**: `#dfdfdf`
  - Used for: All text content, button labels
  - Description: Light gray/off-white for optimal readability on dark backgrounds

- **Secondary Text**: `#9d9d9d`
  - Used for: Placeholder text, empty states, less important information
  - Description: Medium-light gray for de-emphasized content

### Accent Colors

#### Blueish Gray (Primary Accent)
- **Base Accent**: `#4a5568`
  - Used for: Primary buttons, hover states, focused elements
  - Description: Subtle blueish-gray that adds depth without being too colorful

- **Accent Hover**: `#5a6c7d`
  - Used for: Hover state for primary buttons
  - Description: Lighter variation of the base accent for interactive feedback

#### Active/Selected State
- **Active Background**: `#9d9d9d`
  - Used for: Active tabs, selected navigation items
  - Description: Light gray for clearly indicating selected states

- **Active Text**: `#414141`
  - Used for: Text on active/selected elements
  - Description: Dark gray text on light backgrounds for contrast

#### Additional Accent Colors (For Variety)
When multiple distinct UI elements need different colors while maintaining the greyish aesthetic:

- **Greenish Gray**: `#4a5d54`
  - Used for: Success states, positive actions, alternative primary buttons
  - Description: Muted green-gray for positive feedback
  - Hover: `#5a6d64`

- **Warm Gray**: `#5d544a`
  - Used for: Warning states, alternative actions
  - Description: Muted warm gray for secondary emphasis
  - Hover: `#6d645a`

- **Cool Gray**: `#4a5460`
  - Used for: Info states, tertiary actions
  - Description: Muted cool gray for informational elements
  - Hover: `#5a6470`

### Semantic Colors

#### Danger/Delete
- **Base**: `#8b4545`
  - Used for: Delete buttons, destructive actions
  - Description: Muted red for dangerous operations

- **Hover**: `#6b3535`
  - Used for: Hover state for delete buttons
  - Description: Darker muted red

### Gradients

#### Header Gradient
- **Gradient**: `linear-gradient(135deg, #606060 0%, #414141 100%)`
  - Used for: Application header
  - Description: Subtle gradient from medium to dark gray

## Usage Guidelines

### Do's
- ✅ Use the defined color palette consistently across components
- ✅ Maintain high contrast ratios for accessibility (light text on dark backgrounds)
- ✅ Use blueish-gray accent for primary interactive elements
- ✅ Use the additional accent colors (greenish/warm/cool gray) when you need variety while maintaining the aesthetic
- ✅ Use semantic colors (danger red) only for their intended purposes
- ✅ Test color combinations for readability

### Don'ts
- ❌ Don't introduce new colors without updating this documentation
- ❌ Don't use pure black (`#000000`) or pure white (`#ffffff`) - use the defined grays
- ❌ Don't use bright, saturated colors (like bright blue `#667eea`, bright green `#10b981`, bright orange `#f59e0b`) that clash with the minimal aesthetic
- ❌ Don't use colored text for regular content - keep text grayscale

## Accessibility

The color scheme is designed with contrast in mind:
- Text color (`#dfdfdf`) on background (`#414141`) provides good contrast
- Interactive elements use the blueish-gray accent to stand out
- Disabled states use reduced opacity (0.5) to indicate non-interactive elements

## CSS Variables (Future Enhancement)

Consider defining CSS custom properties for easier theming:

```css
:root {
  --color-bg-primary: #414141;
  --color-bg-surface: #606060;
  --color-text-primary: #dfdfdf;
  --color-text-secondary: #9d9d9d;
  --color-accent: #4a5568;
  --color-accent-hover: #5a6c7d;
  --color-active: #9d9d9d;
  --color-danger: #8b4545;
  --color-danger-hover: #6b3535;
}
```

## Examples from Codebase

### Background and Text
```css
.App {
  background-color: #414141;
  color: #dfdfdf;
}
```

### Cards and Surfaces
```css
.card {
  background-color: #606060;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 4px 6px rgba(0,0,0,0.5);
}
```

### Primary Buttons with Accent
```css
.btn-primary {
  background-color: #4a5568;
  color: #dfdfdf;
}

.btn-primary:hover:not(:disabled) {
  background-color: #5a6c7d;
}
```

### Active Navigation Items
```css
.main-nav a.active {
  background-color: #9d9d9d;
  color: #414141;
  font-weight: bold;
}
```

### Danger Buttons
```css
.btn-danger {
  background-color: #8b4545;
  color: #dfdfdf;
}

.btn-danger:hover:not(:disabled) {
  background-color: #6b3535;
}
```
