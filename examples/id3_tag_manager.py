#!/usr/bin/env python3
"""
Script to create test MP3 files with custom ID3 tags for start/end times
"""
import os
import sys
from mutagen.id3 import ID3, TXXX, TIT2, TPE1
from mutagen.mp3 import MP3

def create_test_mp3_with_tags(output_path, start_ms, end_ms):
    """
    Create a minimal MP3 file with ID3 tags for testing.
    Note: This creates a minimal valid MP3 header. For real testing, use actual MP3 files.
    """
    # Minimal MP3 frame (silence frame)
    # This is a valid MPEG1 Layer3 frame with 320kbps, 44100Hz, stereo
    mp3_frame = bytes([
        0xFF, 0xFB, 0x90, 0x00,  # Sync word and header
    ]) + bytes([0x00] * 413)  # Padding to make it 417 bytes (valid frame size)
    
    # Write minimal MP3 file
    with open(output_path, 'wb') as f:
        # Write a few frames to make it valid
        for _ in range(10):
            f.write(mp3_frame)
    
    # Add ID3 tags
    try:
        audio = MP3(output_path)
        
        # Add ID3v2 tags if they don't exist
        if audio.tags is None:
            audio.add_tags()
        
        # Add standard tags
        audio.tags.add(TIT2(encoding=3, text='Test Track'))
        audio.tags.add(TPE1(encoding=3, text='Test Artist'))
        
        # Add custom start time (in milliseconds)
        if start_ms is not None:
            audio.tags.add(TXXX(encoding=3, desc='LAO:MUSIC_START', text=str(start_ms)))
        
        # Add custom end time (in milliseconds)
        if end_ms is not None:
            audio.tags.add(TXXX(encoding=3, desc='LAO:MUSIC_END', text=str(end_ms)))
        
        audio.save()
        print(f"✓ Created {output_path} with start={start_ms}ms, end={end_ms}ms")
        return True
    except Exception as e:
        print(f"✗ Error creating test file: {e}")
        return False

def add_id3_tags_to_existing(file_path, start_ms, end_ms):
    """Add LAO:MUSIC_START and LAO:MUSIC_END tags to an existing MP3 file"""
    try:
        audio = MP3(file_path)
        
        # Initialize tags if they don't exist
        if audio.tags is None:
            audio.add_tags()
        
        # Remove existing custom tags if present
        audio.tags.delall('TXXX:LAO:MUSIC_START')
        audio.tags.delall('TXXX:LAO:MUSIC_END')
        
        # Add custom start time (in milliseconds)
        if start_ms is not None:
            audio.tags.add(TXXX(encoding=3, desc='LAO:MUSIC_START', text=str(start_ms)))
            print(f"  Added LAO:MUSIC_START = {start_ms}ms ({start_ms/1000.0}s)")
        
        # Add custom end time (in milliseconds)
        if end_ms is not None:
            audio.tags.add(TXXX(encoding=3, desc='LAO:MUSIC_END', text=str(end_ms)))
            print(f"  Added LAO:MUSIC_END = {end_ms}ms ({end_ms/1000.0}s)")
        
        audio.save()
        print(f"✓ Updated {file_path}")
        return True
    except Exception as e:
        print(f"✗ Error updating file: {e}")
        return False

def read_id3_tags(file_path):
    """Read and display LAO:MUSIC_START and LAO:MUSIC_END tags from a file"""
    try:
        audio = MP3(file_path)
        
        if audio.tags is None:
            print(f"No ID3 tags found in {file_path}")
            return
        
        print(f"\nID3 Tags in {file_path}:")
        
        # Get all TXXX frames
        txxx_frames = audio.tags.getall('TXXX')
        found_custom_tags = False
        
        for frame in txxx_frames:
            desc = str(frame.desc) if hasattr(frame, 'desc') else ''
            if desc in ['LAO:MUSIC_START', 'LAO:MUSIC_END']:
                value_ms = frame.text[0]
                value_s = float(value_ms) / 1000.0
                print(f"  {desc} = {value_ms}ms ({value_s}s)")
                found_custom_tags = True
        
        if not found_custom_tags:
            print("  No LAO:MUSIC_START or LAO:MUSIC_END tags found")
        
        return True
    except Exception as e:
        print(f"✗ Error reading file: {e}")
        return False

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Manage ID3 tags for custom start/end times')
    parser.add_argument('action', choices=['create', 'add', 'read'], 
                       help='Action to perform')
    parser.add_argument('file', help='MP3 file path')
    parser.add_argument('--start', type=int, help='Start time in milliseconds')
    parser.add_argument('--end', type=int, help='End time in milliseconds')
    
    args = parser.parse_args()
    
    if args.action == 'create':
        if args.start is None or args.end is None:
            print("Error: --start and --end are required for create action")
            sys.exit(1)
        create_test_mp3_with_tags(args.file, args.start, args.end)
    
    elif args.action == 'add':
        if not os.path.exists(args.file):
            print(f"Error: File {args.file} does not exist")
            sys.exit(1)
        add_id3_tags_to_existing(args.file, args.start, args.end)
    
    elif args.action == 'read':
        if not os.path.exists(args.file):
            print(f"Error: File {args.file} does not exist")
            sys.exit(1)
        read_id3_tags(args.file)
