# Contributing to Media Player

Thank you for your interest in contributing to the Media Player project! This document provides guidelines and best practices for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Guidelines](#development-guidelines)
- [Responsive Design Requirements](#responsive-design-requirements)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

Please be respectful and constructive in all interactions. We are committed to providing a welcoming and inclusive environment for all contributors.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR-USERNAME/media-player.git`
3. Create a new branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Test your changes thoroughly
6. Submit a pull request

## Development Guidelines

### Setting Up Your Development Environment

See the [README.md](README.md) for detailed installation instructions. Quick start:

```bash
# Install backend dependencies
cd backend
pip install uv
uv sync --no-build-isolation

# Install frontend dependencies
cd ../frontend
npm install

# Start development servers
# Terminal 1 - Backend
cd backend
uv run python app.py

# Terminal 2 - Frontend (with hot reload)
cd frontend
npm run dev
```

## Responsive Design Requirements

**⚠️ IMPORTANT: All new features and UI components MUST be implemented with responsive design for mobile devices.**

### Why Responsive Design?

The Media Player web interface is accessed from various devices including smartphones, tablets, and desktops. To ensure a consistent and usable experience across all devices, all UI components must be responsive.

### Responsive Design Principles

1. **Mobile-First Approach**: Design for mobile devices first, then enhance for larger screens
2. **Touch-Friendly**: All interactive elements should be easy to tap on mobile devices (minimum 44x44px)
3. **Readable Text**: Font sizes should scale appropriately for different screen sizes
4. **Flexible Layouts**: Use flexbox and grid layouts that adapt to different screen widths
5. **Optimized Navigation**: Navigation should be accessible and usable on small screens

### Standard Breakpoints

Use these standard breakpoints for responsive design:

```css
/* Small mobile devices */
@media (max-width: 480px) {
  /* Styles for phones in portrait mode */
}

/* Tablet and larger mobile devices */
@media (max-width: 768px) {
  /* Styles for tablets and phones in landscape */
}

/* Desktop and larger screens */
@media (min-width: 769px) {
  /* Default desktop styles */
}
```

### Responsive Design Checklist

When implementing new UI features, ensure:

- [ ] **Flexible Layouts**: Components adapt to different screen widths
- [ ] **Stacked Elements**: Horizontal layouts stack vertically on mobile
- [ ] **Touch Targets**: Buttons and interactive elements are at least 44x44px
- [ ] **Readable Text**: Font sizes are appropriate for mobile (minimum 14px for body text)
- [ ] **Scrollable Content**: Long content is scrollable with appropriate max-heights
- [ ] **Hidden/Collapsed Content**: Consider collapsible sections for mobile
- [ ] **Full-Width Buttons**: Action buttons are full-width on mobile for easier tapping
- [ ] **Responsive Tables**: Tables convert to card layouts on mobile
- [ ] **Modal Dialogs**: Modals are sized appropriately for mobile screens (90-95% width)
- [ ] **Form Inputs**: Inputs are sized for easy interaction on mobile

### Responsive Design Patterns

#### 1. Flexible Header/Action Buttons

```css
.component-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.component-actions {
  display: flex;
  gap: 10px;
}

@media (max-width: 768px) {
  .component-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }
  
  .component-actions {
    width: 100%;
    flex-direction: column;
  }
  
  .component-actions button {
    width: 100%;
  }
}
```

#### 2. Responsive Tables to Cards

```css
/* Desktop: normal table */
.data-table table {
  width: 100%;
}

/* Mobile: convert to cards */
@media (max-width: 768px) {
  .data-table thead {
    display: none;
  }
  
  .data-table tbody tr {
    display: block;
    margin-bottom: 15px;
    border: 1px solid #ccc;
    border-radius: 8px;
    padding: 12px;
  }
  
  .data-table td {
    display: block;
    text-align: left;
    padding: 8px 0;
  }
  
  .data-table td::before {
    content: attr(data-label);
    font-weight: 600;
    display: block;
    margin-bottom: 4px;
  }
}
```

#### 3. Modal Dialogs

```css
.modal-content {
  max-width: 600px;
  width: 90%;
}

@media (max-width: 768px) {
  .modal-content {
    width: 95%;
    max-height: 90vh;
    padding: 20px;
  }
}
```

### Examples

See these files for reference implementations of responsive design:

- **MusicManager**: [frontend/src/components/MusicManager.tsx](frontend/src/components/MusicManager.tsx) and [MusicManager.css](frontend/src/components/MusicManager.css)
- **App Layout**: [frontend/src/App.css](frontend/src/App.css)

## Coding Standards

### TypeScript/React

- Use functional components with hooks
- Use TypeScript for type safety
- Follow existing naming conventions
- Use meaningful variable and function names
- Add comments for complex logic
- Keep components focused and reusable

### Python

- Follow PEP 8 style guide
- Use type hints where appropriate
- Write docstrings for functions and classes
- Keep functions focused and single-purpose

### CSS

- Use BEM-like naming conventions for classes
- Group related styles together
- Add comments for complex styling
- **Always include responsive styles with media queries**
- Use CSS variables for colors and repeated values when appropriate

## Testing

Before submitting a pull request:

1. **Test on Multiple Screen Sizes**: Test your changes on:
   - Mobile devices (< 480px width)
   - Tablets (480px - 768px width)
   - Desktop (> 768px width)

2. **Browser Testing**: Test on major browsers:
   - Chrome/Edge
   - Firefox
   - Safari

3. **Run Backend Tests** (if applicable):
   ```bash
   cd backend
   pytest tests/
   ```

4. **Check for Build Errors**:
   ```bash
   cd frontend
   npm run build
   ```

5. **Manual Testing**: Test the actual functionality of your changes in a running application

## Pull Request Process

1. **Update Documentation**: If you're adding new features, update the README.md and any relevant documentation
2. **Add Tests**: Add or update tests as necessary
3. **Verify Responsive Design**: Include screenshots or descriptions of responsive behavior
4. **Clear Commit Messages**: Write clear, descriptive commit messages
5. **Reference Issues**: Reference any related issues in your PR description
6. **Request Review**: Request review from maintainers

### Pull Request Template

When creating a pull request, include:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] UI/UX improvement

## Responsive Design
- [ ] Tested on mobile devices (< 480px)
- [ ] Tested on tablets (480px - 768px)
- [ ] Tested on desktop (> 768px)
- [ ] All interactive elements are touch-friendly
- [ ] Text is readable on all screen sizes

## Testing
- [ ] Tested locally
- [ ] All tests pass
- [ ] No build errors

## Screenshots
(If applicable, add screenshots showing responsive behavior)
```

## Questions or Issues?

If you have questions or run into issues:

1. Check existing documentation in the [docs/](docs/) directory
2. Search existing issues on GitHub
3. Open a new issue with a detailed description

Thank you for contributing to Media Player! 🎵
