# GitHub Actions Workflows

This directory contains automated workflows for the Media Player project.

## Available Workflows

### Release Build (Automatic)

**File:** `release.yml`

**Trigger:** Automatic on release creation/publication

**Purpose:** Automatically builds and attaches the Windows executable to GitHub releases.

#### How to Use

1. Go to the **Releases** section in the GitHub repository
2. Click **"Create a new release"** or **"Draft a new release"**
3. Choose or create a new tag (e.g., `v1.0.0`)
4. Fill in the release title and description
5. Click **"Publish release"**
6. The workflow runs automatically and attaches the executable to the release

#### What It Does

1. Detects when a new release is created or published
2. Sets up Python 3.13 and Node.js 20
3. Installs all dependencies
4. Builds the React frontend
5. Creates a Windows executable using PyInstaller
6. Uploads the executable as a release asset with the naming format: `media-player-windows-[tag]-[filename]`

#### Output

The executable is automatically attached to the release as:
- `media-player-windows-v1.0.0-media-player.exe` (for single-file bundle), or
- `media-player-windows-v1.0.0-media-player.zip` (for one-dir bundle)

#### Downloading

1. Go to the **Releases** page
2. Find your release
3. Download the Windows executable from the release assets
4. Extract (if ZIP) and run `media-player.exe`

#### Build Time

Typical build time: 5-10 minutes

### Run Tests

**File:** `test.yml`

**Trigger:** Automatic on push/PR to main/develop branches, or manual (workflow_dispatch)

**Purpose:** Runs the pytest test suite across multiple platforms and Python versions.

#### What It Does

1. **Multi-platform testing:**
   - Tests on Ubuntu, Windows, and macOS
   - Tests with Python 3.12 and 3.13
   
2. **Unit tests:**
   - Runs all tests in `backend/tests/`
   - Generates JUnit XML test results
   - Uploads test results as artifacts
   
3. **Coverage report:**
   - Runs tests with coverage tracking
   - Generates HTML and XML coverage reports
   - Uploads coverage reports as artifacts

#### Test Results

After the workflow completes, you can:
- View test results in the workflow summary
- Download test result XML files from artifacts
- Download HTML coverage reports from artifacts

#### Build Time

Typical run time: 3-5 minutes per platform/Python combination

### Build Windows Executable (Manual)

**File:** `build-windows-exe.yml`

**Trigger:** Manual (workflow_dispatch)

**Purpose:** Creates a standalone Windows executable (.exe) bundle with the built frontend included. Use this for testing builds without creating a release.

#### How to Use

1. Go to the **Actions** tab in the GitHub repository
2. Select **"Build Windows Executable"** from the left sidebar
3. Click the **"Run workflow"** button
4. (Optional) Enter a version tag (e.g., `v1.0.0`, `2024-01-15`)
5. Click **"Run workflow"** to start the build

#### What It Does

1. Sets up Python 3.13 and Node.js 20
2. Installs all dependencies
3. Builds the React frontend
4. Creates a Windows executable using PyInstaller
5. Uploads the complete bundle as a downloadable artifact

#### Output

The workflow produces two artifacts:

1. **media-player-windows-[version/date]**
   - Contains the complete executable bundle
   - Includes `media-player.exe` and all dependencies
   - Ready to distribute to end users

2. **media-player-windows-[version/date]-release-notes**
   - Contains build information and usage instructions
   - Includes commit hash and build date

#### Downloading the Build

1. After the workflow completes, go to the workflow run page
2. Scroll down to the **Artifacts** section
3. Click on the artifact name to download
4. Extract the ZIP file
5. Run `media-player.exe`

#### Build Time

Typical build time: 5-10 minutes

#### Requirements

- None for running the workflow (GitHub Actions provides all build tools)
- For running the built executable: Windows 10 or later

## Notes

- Artifacts are retained for 30 days by default
- Each workflow run creates a unique artifact with a timestamp
- The executable is completely standalone - no Python installation needed by end users
- The frontend is pre-built and included in the executable

## Troubleshooting

If the workflow fails:

1. Check the workflow logs for error messages
2. Verify that `backend/media-player.spec` exists
3. Ensure frontend builds successfully (check `backend/static/` folder)
4. Review the [Bundling Guide](../docs/technical/bundling.md) for detailed requirements

## Future Workflows

Potential future workflows could include:
- Unix/Linux distribution packages
- Multi-platform builds
- Integration tests with running server
- UI screenshot generation and comparison
