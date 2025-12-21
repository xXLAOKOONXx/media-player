#!/usr/bin/env python3
"""
UI Screenshot Generator for Documentation

This script generates screenshots of the media player UI for user documentation.
It uses Playwright to automate a browser and capture screenshots of different UI states.

Requirements:
    pip install playwright
    playwright install chromium
"""

import os
import sys
import time
import argparse
from pathlib import Path

# Check if optional dependencies are available
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        from playwright.sync_api import sync_playwright
        return True
    except ImportError:
        print("Error: Playwright is not installed.")
        print("Install it with:")
        print("  pip install playwright")
        print("  playwright install chromium")
        return False


def wait_for_server(url, timeout=30):
    """Wait for the server to be available."""
    if not REQUESTS_AVAILABLE:
        print("Warning: requests module not available, skipping server check")
        return True
    
    print(f"Waiting for server at {url}...")
    start_time = time.time()
    
    print(f"Waiting for server at {url}...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                print("Server is ready!")
                return True
        except requests.exceptions.RequestException:
            time.sleep(1)
    
    print(f"Error: Server did not respond within {timeout} seconds")
    return False


def generate_screenshots(output_dir, base_url="http://localhost:5000"):
    """Generate screenshots of the UI."""
    from playwright.sync_api import sync_playwright
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"\nGenerating screenshots to: {output_path}")
    print("=" * 60)
    
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()
        
        screenshots_taken = []
        
        try:
            # 1. Main page / Player tab
            print("1. Capturing main player interface...")
            page.goto(base_url)
            page.wait_for_timeout(2000)  # Wait for UI to load
            screenshot_path = output_path / "01_player_tab.png"
            page.screenshot(path=str(screenshot_path))
            screenshots_taken.append(screenshot_path)
            print(f"   ✓ Saved: {screenshot_path.name}")
            
            # 2. Storage tab (if exists)
            print("2. Capturing storage management...")
            try:
                # Look for storage tab button
                storage_button = page.locator("text=Storage").first
                if storage_button.is_visible(timeout=2000):
                    storage_button.click()
                    page.wait_for_timeout(1000)
                    screenshot_path = output_path / "02_storage_tab.png"
                    page.screenshot(path=str(screenshot_path))
                    screenshots_taken.append(screenshot_path)
                    print(f"   ✓ Saved: {screenshot_path.name}")
            except Exception as e:
                print(f"   ⚠ Skipped (not available): {e}")
            
            # 3. Playlists tab
            print("3. Capturing playlists management...")
            try:
                playlists_button = page.locator("text=Playlists").first
                if playlists_button.is_visible(timeout=2000):
                    playlists_button.click()
                    page.wait_for_timeout(1000)
                    screenshot_path = output_path / "03_playlists_tab.png"
                    page.screenshot(path=str(screenshot_path))
                    screenshots_taken.append(screenshot_path)
                    print(f"   ✓ Saved: {screenshot_path.name}")
            except Exception as e:
                print(f"   ⚠ Skipped (not available): {e}")
            
            # 4. Sound Effects tab (if exists)
            print("4. Capturing sound effects...")
            try:
                sound_effects_button = page.locator("text=Sound Effects").first
                if sound_effects_button.is_visible(timeout=2000):
                    sound_effects_button.click()
                    page.wait_for_timeout(1000)
                    screenshot_path = output_path / "04_sound_effects_tab.png"
                    page.screenshot(path=str(screenshot_path))
                    screenshots_taken.append(screenshot_path)
                    print(f"   ✓ Saved: {screenshot_path.name}")
            except Exception as e:
                print(f"   ⚠ Skipped (not available): {e}")
            
            # 5. Music tab (if exists)
            print("5. Capturing music management...")
            try:
                music_button = page.locator("text=Music").first
                if music_button.is_visible(timeout=2000):
                    music_button.click()
                    page.wait_for_timeout(1000)
                    screenshot_path = output_path / "05_music_tab.png"
                    page.screenshot(path=str(screenshot_path))
                    screenshots_taken.append(screenshot_path)
                    print(f"   ✓ Saved: {screenshot_path.name}")
            except Exception as e:
                print(f"   ⚠ Skipped (not available): {e}")
            
            # 6. Full page screenshot
            print("6. Capturing full page...")
            page.goto(base_url)
            page.wait_for_timeout(1000)
            screenshot_path = output_path / "00_overview.png"
            page.screenshot(path=str(screenshot_path), full_page=True)
            screenshots_taken.append(screenshot_path)
            print(f"   ✓ Saved: {screenshot_path.name}")
            
        except Exception as e:
            print(f"\nError during screenshot generation: {e}")
            return False
        finally:
            browser.close()
    
    print("\n" + "=" * 60)
    print(f"✓ Generated {len(screenshots_taken)} screenshots")
    print(f"\nScreenshots saved to: {output_path.absolute()}")
    
    # Generate markdown documentation
    generate_screenshot_docs(output_path, screenshots_taken)
    
    return True


def generate_screenshot_docs(output_dir, screenshots):
    """Generate a markdown file documenting the screenshots."""
    doc_path = output_dir / "SCREENSHOTS.md"
    
    with open(doc_path, 'w') as f:
        f.write("# UI Screenshots\n\n")
        f.write("This directory contains screenshots of the media player user interface.\n\n")
        f.write("## Screenshots\n\n")
        
        for screenshot in sorted(screenshots):
            name = screenshot.stem.replace('_', ' ').title()
            f.write(f"### {name}\n\n")
            f.write(f"![{name}](./{screenshot.name})\n\n")
    
    print(f"✓ Generated documentation: {doc_path.name}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate UI screenshots for documentation"
    )
    parser.add_argument(
        "--output",
        default="docs/screenshots",
        help="Output directory for screenshots (default: docs/screenshots)"
    )
    parser.add_argument(
        "--url",
        default="http://localhost:5000",
        help="Base URL of the application (default: http://localhost:5000)"
    )
    parser.add_argument(
        "--no-wait",
        action="store_true",
        help="Don't wait for server, assume it's already running"
    )
    
    args = parser.parse_args()
    
    print("UI Screenshot Generator")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Wait for server to be ready (unless --no-wait is specified)
    if not args.no_wait:
        if not wait_for_server(args.url):
            print("\nPlease start the server first:")
            print("  cd backend && python app.py")
            sys.exit(1)
    
    # Generate screenshots
    success = generate_screenshots(args.output, args.url)
    
    if success:
        print("\n✓ Screenshot generation completed successfully!")
        sys.exit(0)
    else:
        print("\n✗ Screenshot generation failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
