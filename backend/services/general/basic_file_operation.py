"""
Basic File Operations Service
Provides utility functions for file path operations
"""

import os
from pathlib import Path
import logging

logger = logging.getLogger('BasicFileOperation')


def get_actual_path_with_correct_case(file_path: str) -> str:
    """Get the actual path with correct upper/lower case letters.
    
    On case-insensitive filesystems (Windows), this ensures we get the actual
    casing as stored on disk.
    
    Args:
        file_path: Path to resolve
        
    Returns:
        The actual path with correct casing, or the original path if unable to resolve
    """
    try:
        # First ensure we have an absolute path
        abs_path = os.path.abspath(file_path)
        
        # Check if the file exists
        if not os.path.exists(abs_path):
            return abs_path
        
        # On Windows, we can use the actual case from the filesystem
        # Convert to Path object and resolve to get the real path
        real_path = Path(abs_path).resolve()
        
        # On Windows, we need to walk the path to get the correct case
        # This is needed because resolve() doesn't always return the correct case
        if os.name == 'nt':
            # Split the path into parts
            parts = list(real_path.parts)
            if not parts:
                return str(real_path)
            
            # Start with the root (e.g., 'C:\\')
            current = Path(parts[0])
            
            # Walk through each part and find the actual case
            for part in parts[1:]:
                if not current.exists():
                    # If we can't continue, return what we have
                    return str(current / part)
                
                # List the directory and find the matching entry with correct case
                try:
                    entries = list(current.iterdir())
                    matched = None
                    for entry in entries:
                        if entry.name.lower() == part.lower():
                            matched = entry
                            break
                    
                    if matched:
                        current = matched
                    else:
                        # If no match found, append as-is
                        current = current / part
                except (PermissionError, OSError):
                    # If we can't list the directory, append as-is
                    current = current / part
            
            return str(current)
        else:
            # On Unix-like systems, the filesystem is usually case-sensitive
            # so resolve() should give us the correct path
            return str(real_path)
    except Exception as e:
        logger.debug(f"Failed to get actual path case for {file_path}: {e}")
        # Fall back to the absolute path if anything goes wrong
        return os.path.abspath(file_path)
