# Testing Guide

This document describes the testing infrastructure and how to run tests for the media player.

## Test Structure

```
media-player/
├── backend/
│   └── tests/           # Backend unit and integration tests
│       ├── __init__.py
│       ├── conftest.py  # Pytest fixtures and configuration
│       ├── test_api.py  # API endpoint tests
│       ├── test_crossfade.py  # Audio crossfade tests
│       ├── test_music.py      # Music management tests
│       └── test_e2e.py        # End-to-end integration tests
├── examples/
│   └── example_tracks/  # Test audio files
│       ├── test_track.mp3
│       └── README.md
├── scripts/
│   └── generate_screenshots.py  # UI screenshot generator
├── run_tests.sh         # Unix/Linux test runner
└── run_tests.bat        # Windows test runner
```

## Running Tests

### Quick Start

**Unix/Linux/macOS:**
```bash
./run_tests.sh
```

**Windows:**
```cmd
run_tests.bat
```

### Manual Test Execution

**Install pytest:**
```bash
cd backend
pip install pytest
# or with uv
uv pip install pytest
```

**Run all tests:**
```bash
cd backend
pytest tests/
```

**Run specific test file:**
```bash
cd backend
pytest tests/test_api.py
```

**Run specific test class:**
```bash
cd backend
pytest tests/test_api.py::TestPlaybackAPI
```

**Run specific test:**
```bash
cd backend
pytest tests/test_api.py::TestPlaybackAPI::test_status_endpoint
```

**Run with verbose output:**
```bash
cd backend
pytest tests/ -v
```

**Run with coverage:**
```bash
cd backend
pip install pytest-cov
pytest tests/ --cov=. --cov-report=html
```

## Test Categories

### Unit Tests

Test individual components in isolation:
- `test_crossfade.py` - Audio metadata extraction, crossfade configuration
- `test_music.py` - Music manager functionality

**Run unit tests:**
```bash
cd backend
pytest tests/test_crossfade.py tests/test_music.py
```

### API Tests

Test REST API endpoints (requires running server):
- `test_api.py` - API endpoint tests

**Run API tests:**
```bash
# Terminal 1: Start the server
cd backend
python app.py

# Terminal 2: Run tests
cd backend
pytest tests/test_api.py
```

### End-to-End Tests

Test complete workflows (requires running server):
- `test_e2e.py` - End-to-end integration tests

**Run E2E tests:**
```bash
# Terminal 1: Start the server
cd backend
python app.py

# Terminal 2: Run tests
cd backend
pytest tests/test_e2e.py
```

## Test Fixtures

The `conftest.py` file provides common fixtures:

- `test_audio_file` - Path to test MP3 file
- `temp_dir` - Temporary directory for test files
- `sample_playlist` - Pre-created M3U playlist
- `sample_config` - Sample configuration dictionary
- `mock_storage_path` - Mock storage directory structure

**Example usage:**
```python
def test_something(test_audio_file, temp_dir):
    # test_audio_file points to examples/example_tracks/test_track.mp3
    # temp_dir is a temporary directory that will be cleaned up
    pass
```

## Writing New Tests

### Test File Naming

- Test files must start with `test_` (e.g., `test_feature.py`)
- Test functions must start with `test_` (e.g., `def test_something()`)
- Test classes should start with `Test` (e.g., `class TestFeature`)

### Example Test

```python
import pytest

class TestNewFeature:
    """Test new feature functionality."""
    
    def test_basic_functionality(self, test_audio_file):
        """Test basic feature behavior."""
        # Arrange
        expected = "expected_value"
        
        # Act
        result = perform_action(test_audio_file)
        
        # Assert
        assert result == expected, f"Expected {expected}, got {result}"
    
    def test_error_handling(self):
        """Test error handling."""
        with pytest.raises(ValueError):
            perform_invalid_action()
```

### Best Practices

1. **Isolation**: Tests should not depend on each other
2. **Cleanup**: Use fixtures and temp directories for file operations
3. **Clear names**: Use descriptive test names that explain what is tested
4. **Arrange-Act-Assert**: Structure tests clearly
5. **Skip wisely**: Use `pytest.skip()` when external dependencies are not available
6. **Mock external services**: Use mocking for network calls, file systems, etc.

## Continuous Integration

The project uses GitHub Actions for automated testing.

### Test Workflow

**File:** `.github/workflows/test.yml`

**Triggers:**
- Automatically on push to `main` or `develop` branches
- Automatically on pull requests to `main` or `develop` branches
- Manually via workflow_dispatch

**What it tests:**
- Multi-platform: Ubuntu, Windows, and macOS
- Multi-version: Python 3.12 and 3.13
- All unit tests in `backend/tests/`
- Coverage reporting

**Artifacts:**
- Test results (JUnit XML) for each platform/Python combination
- Code coverage report (HTML and XML)

**Viewing Results:**
1. Go to the **Actions** tab in the GitHub repository
2. Select a workflow run
3. View the test summary in the workflow page
4. Download artifacts (test results and coverage reports) from the artifacts section

See `.github/workflows/test.yml` for the complete workflow configuration.

## UI Testing

### Screenshot Generation

Generate UI screenshots for documentation:

```bash
# Start the server
cd backend
python app.py

# In another terminal, generate screenshots
python scripts/generate_screenshots.py
```

Screenshots are saved to `docs/screenshots/` with documentation.

**Requirements:**
```bash
pip install playwright requests
playwright install chromium
```

## Troubleshooting

### Tests Fail Due to Missing Server

Some tests require the Flask server to be running:

```bash
# Terminal 1
cd backend
python app.py

# Terminal 2
cd backend
pytest tests/test_api.py
```

### Tests Fail Due to Missing Audio File

Ensure test audio files exist:
```bash
ls examples/example_tracks/test_track.mp3
```

### Pytest Not Found

Install pytest:
```bash
cd backend
pip install pytest
# or
uv pip install pytest
```

### Import Errors

Make sure you're in the correct directory:
```bash
cd backend
pytest tests/
```

## Test Coverage

To measure test coverage:

```bash
cd backend
pip install pytest-cov
pytest tests/ --cov=. --cov-report=html
```

Open `htmlcov/index.html` in a browser to view the coverage report.

## Performance Testing

For performance testing, use the `monitor_performance.py` script:

```bash
cd examples
python monitor_performance.py
```

## Legacy Test Files

The following test files in `examples/` are kept for reference but should be migrated to the new structure:
- `test_id3_support.py` - ID3 tag support testing
- `test_shuffle_first_track.py` - Shuffle mode testing
- `test_track_times.py` - Track timing functionality

These scripts can be run directly but are not part of the automated test suite.
