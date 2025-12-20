# Using uv for Python Environment Management

This project supports [uv](https://github.com/astral-sh/uv), a fast Python package installer and environment manager.

## Installing uv

### On macOS and Linux:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### On Windows:
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Using pip:
```bash
pip install uv
```

## Setting Up the Backend with uv

### 1. Create a virtual environment
```bash
cd backend
uv venv
```

This creates a `.venv` directory in the backend folder.

### 2. Activate the virtual environment

**Linux/macOS:**
```bash
source .venv/bin/activate
```

**Windows:**
```powershell
.venv\Scripts\activate
```

### 3. Install dependencies

Using `pyproject.toml`:
```bash
uv pip install -e .
```

Or using `requirements.txt` (backward compatible):
```bash
uv pip install -r requirements.txt
```

### 4. Install development dependencies (optional)
```bash
uv pip install -e ".[dev]"
```

## Why uv?

### Speed
- **10-100x faster** than pip for installing packages
- Uses a global cache to avoid re-downloading packages
- Parallel downloads and installations

### Reliability
- Consistent dependency resolution
- Better conflict detection
- Reproducible environments

### Comparison

| Operation | pip | uv | Improvement |
|-----------|-----|-----|-------------|
| Install Flask | ~2s | ~0.2s | 10x faster |
| Install all deps | ~15s | ~1s | 15x faster |
| Cold cache | ~30s | ~3s | 10x faster |

## Running the Application

After setting up with uv:

```bash
cd backend
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
python app.py
```

## Backward Compatibility

The project maintains both:
- `pyproject.toml` for uv and modern Python tools
- `requirements.txt` for traditional pip users

Both files are kept in sync. You can use either:

```bash
# Traditional pip
pip install -r requirements.txt

# Modern uv
uv pip install -e .
```

## Development Workflow

```bash
# Create environment
uv venv

# Activate
source .venv/bin/activate

# Install with dev dependencies
uv pip install -e ".[dev]"

# Run tests (when available)
pytest

# Format code
black .

# Lint code
flake8 .
```

## Updating Dependencies

### Adding a new dependency:
```bash
# Add to pyproject.toml [project.dependencies]
uv pip install package-name

# Or update requirements.txt and sync
uv pip compile pyproject.toml -o requirements.txt
```

### Upgrading all dependencies:
```bash
uv pip install --upgrade -e .
```

## Raspberry Pi Deployment

On Raspberry Pi, you can use uv for faster deployments:

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone repository
git clone https://github.com/xXLAOKOONXx/media-player.git
cd media-player/backend

# Setup environment (much faster than pip!)
uv venv
source .venv/bin/activate
uv pip install -e .

# Run
python app.py
```

## Troubleshooting

### uv not found after installation
```bash
# Add to PATH (typically done automatically)
export PATH="$HOME/.cargo/bin:$PATH"

# Or reinstall
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Permission errors
```bash
# Don't use sudo with uv
# It manages environments in user space
```

### Compatibility issues
```bash
# Fall back to pip if needed
pip install -r requirements.txt
```

## Additional Resources

- [uv Documentation](https://github.com/astral-sh/uv)
- [pyproject.toml Specification](https://packaging.python.org/en/latest/specifications/pyproject-toml/)
- [Python Packaging Guide](https://packaging.python.org/)
