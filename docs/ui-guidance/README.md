# UI Guidance

This folder contains guidance on setting up and styling UI elements in the Media Player application.

## Design Principles

The Media Player follows these core UI/UX principles:

1. **Dark Mode First** - The application is designed with dark mode as the default and primary theme
2. **Icon-Driven Interface** - Prefer using icons over text labels for actions and navigation when possible
3. **Material Design** - Use Material Icons for consistency across the application
4. **Minimal Color Palette** - Use a restricted color palette based on grayscale with subtle accent colors

## Guidelines

- [**Colors**](colors.md) - Color scheme and usage guidelines
- [**Icons**](icons.md) - Icon usage and Material Icons guidelines
- [**Dark Mode**](dark-mode.md) - Dark mode implementation and best practices

## Quick Reference

### Color Palette
- **Background**: `#414141` (dark gray)
- **Card/Surface**: `#606060` (medium gray)
- **Text**: `#dfdfdf` (light gray/white)
- **Accent**: `#4a5568` (blueish gray)
- **Accent Hover**: `#5a6c7d` (lighter blueish gray)

### Typography
- Font family: System fonts (-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', etc.)
- Font smoothing enabled for better rendering

### Icons
- **Library**: Material Icons (via `material-icons` npm package)
- **Usage**: Prefer icons over text labels for actions
- **Class**: Use `material-icons` class with icon name as content

## Note for Developers

When adding new UI components or modifying existing ones:
- Follow the established color scheme
- Use Material Icons when representing actions or states
- Maintain dark mode compatibility
- Test on both desktop and mobile viewports
- Keep the UI minimal and focused
