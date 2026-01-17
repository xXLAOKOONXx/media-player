#!/usr/bin/env python3
"""
Fix file_path and media_id in media-player-stats.db

This script fixes file_paths that have incorrect casing and updates
the corresponding media_id values which are based on the normalized path.

The media_id is calculated as: SHA256(os.path.normpath(file_path).encode('utf-8'))
"""

import sqlite3
import os
import hashlib
import sys
from pathlib import Path


def calculate_media_id(file_path):
    """Calculate media_id from a file path (same logic as the app)"""
    normalized_path = os.path.normpath(file_path)
    return hashlib.sha256(normalized_path.encode('utf-8', errors='replace')).hexdigest()


def find_actual_file_path(incorrect_path):
    """Try to find the actual file on disk with correct casing"""
    # First check if the path exists as-is
    if os.path.exists(incorrect_path):
        # Get the actual path with correct casing
        # On Windows, resolve the path to get the actual case
        try:
            # Try to resolve to actual case
            resolved = Path(incorrect_path).resolve()
            if resolved.exists():
                return str(resolved)
        except Exception:
            pass
        return incorrect_path
    
    # If the file doesn't exist, try to find it with case-insensitive search
    try:
        path = Path(incorrect_path)
        parent = path.parent
        filename = path.name
        
        if parent.exists():
            # List all files in the parent directory and match case-insensitively
            for entry in parent.iterdir():
                if entry.name.lower() == filename.lower():
                    return str(entry.resolve())
    except Exception as e:
        print(f"  Warning: Could not search for file: {e}")
    
    return None


def fix_stats_database(db_path, dry_run=True):
    """Fix file_paths and media_ids in the stats database
    
    Args:
        db_path: Path to the media-player-stats.db file
        dry_run: If True, only report what would be changed without making changes
    """
    if not os.path.exists(db_path):
        print(f"Error: Database file not found: {db_path}")
        return False
    
    print(f"Opening database: {db_path}")
    conn = sqlite3.connect(db_path, timeout=5.0)
    cursor = conn.cursor()
    
    # Check if the table exists and get its schema
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='media_stats'")
    if not cursor.fetchone():
        print("Error: media_stats table not found in database")
        conn.close()
        return False
    
    # Get column names
    cursor.execute('PRAGMA table_info(media_stats)')
    columns = {row[1] for row in cursor.fetchall()}
    
    # Determine which path column is used
    path_column = 'file_path' if 'file_path' in columns else 'folder_path'
    has_media_id = 'media_id' in columns
    
    print(f"Using column: {path_column}")
    print(f"Has media_id column: {has_media_id}")
    print()
    
    # Get all distinct file paths
    cursor.execute(f'SELECT DISTINCT {path_column} FROM media_stats WHERE {path_column} IS NOT NULL')
    distinct_paths = [row[0] for row in cursor.fetchall()]
    
    print(f"Found {len(distinct_paths)} distinct file paths in database")
    print()
    
    changes = []
    not_found = []
    already_correct = []
    
    for old_path in distinct_paths:
        if not old_path:
            continue
        
        # Find the actual file path with correct casing
        correct_path = find_actual_file_path(old_path)
        
        if correct_path is None:
            not_found.append(old_path)
            print(f"⚠ File not found: {old_path}")
            continue
        
        # Normalize both paths for comparison
        old_normalized = os.path.normpath(old_path)
        correct_normalized = os.path.normpath(correct_path)
        
        # Check if the path needs to be updated
        if old_normalized == correct_normalized:
            already_correct.append(old_path)
            continue
        
        # Calculate media_ids
        old_media_id = calculate_media_id(old_path)
        new_media_id = calculate_media_id(correct_path)
        
        changes.append({
            'old_path': old_path,
            'new_path': correct_path,
            'old_media_id': old_media_id,
            'new_media_id': new_media_id
        })
        
        print(f"✓ Found mismatch:")
        print(f"  Old: {old_path}")
        print(f"  New: {correct_path}")
        if has_media_id:
            print(f"  Old media_id: {old_media_id}")
            print(f"  New media_id: {new_media_id}")
        print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total distinct paths: {len(distinct_paths)}")
    print(f"Already correct: {len(already_correct)}")
    print(f"Need fixing: {len(changes)}")
    print(f"Files not found: {len(not_found)}")
    print()
    
    if changes:
        if dry_run:
            print("DRY RUN MODE - No changes will be made")
            print("Run with --apply to make these changes")
        else:
            print("Applying changes...")
            
            for change in changes:
                try:
                    # Update the path
                    cursor.execute(
                        f'UPDATE media_stats SET {path_column} = ? WHERE {path_column} = ?',
                        (change['new_path'], change['old_path'])
                    )
                    
                    # Update media_id if the column exists
                    if has_media_id:
                        cursor.execute(
                            f'UPDATE media_stats SET media_id = ? WHERE {path_column} = ?',
                            (change['new_media_id'], change['new_path'])
                        )
                    
                    print(f"✓ Updated: {change['old_path']}")
                except Exception as e:
                    print(f"✗ Error updating {change['old_path']}: {e}")
            
            conn.commit()
            print()
            print(f"Successfully updated {len(changes)} file paths")
    
    conn.close()
    return True


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Fix file_path and media_id in media-player-stats.db'
    )
    parser.add_argument(
        'db_path',
        nargs='?',
        help='Path to media-player-stats.db (default: auto-detect from config)'
    )
    parser.add_argument(
        '--apply',
        action='store_true',
        help='Actually apply the changes (default is dry-run)'
    )
    
    args = parser.parse_args()
    
    # Try to auto-detect database path if not provided
    if not args.db_path:
        # Try common locations
        possible_paths = [
            'media-player-stats.db',
            'backend/media-player-stats.db',
            os.path.expanduser('~/.config/media-player/media-player-stats.db'),
        ]
        
        # Try to load from config
        try:
            import json
            config_path = 'config.json'
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    stats_folder = config.get('stats_folder')
                    if stats_folder:
                        possible_paths.insert(0, os.path.join(stats_folder, 'media-player-stats.db'))
        except Exception:
            pass
        
        for path in possible_paths:
            if os.path.exists(path):
                args.db_path = path
                print(f"Auto-detected database: {path}")
                print()
                break
        
        if not args.db_path:
            print("Error: Could not find media-player-stats.db")
            print("Please specify the path explicitly:")
            print(f"  python {sys.argv[0]} /path/to/media-player-stats.db")
            return 1
    
    success = fix_stats_database(args.db_path, dry_run=not args.apply)
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
