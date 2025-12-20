#!/usr/bin/env python3
"""
Test script for Flask API endpoints
"""
import requests
import json
import time
import os
import sys

API_BASE = "http://localhost:5000"

def test_status_endpoint():
    """Test the status endpoint"""
    print("Testing GET /api/playback/status...")
    response = requests.get(f"{API_BASE}/api/playback/status")
    
    if response.status_code != 200:
        print(f"✗ Status: {response.status_code}")
        return False
    
    data = response.json()
    print(f"✓ Status endpoint working")
    print(f"  Response: {json.dumps(data, indent=2)}")
    return True

def test_tracks_endpoint():
    """Test the tracks endpoint"""
    print("\nTesting GET /api/playback/tracks...")
    response = requests.get(f"{API_BASE}/api/playback/tracks")
    
    if response.status_code != 200:
        print(f"✗ Status: {response.status_code}")
        return False
    
    data = response.json()
    print(f"✓ Tracks endpoint working")
    print(f"  Found {len(data.get('tracks', []))} tracks")
    return True

def test_set_track_times():
    """Test setting track times"""
    print("\nTesting PUT /api/playback/tracks/0/times...")
    
    # First, make sure we have a playlist loaded
    response = requests.get(f"{API_BASE}/api/playback/tracks")
    tracks = response.json().get('tracks', [])
    
    if len(tracks) == 0:
        print("⚠ No playlist loaded, skipping track times test")
        return True
    
    # Set custom times for first track
    response = requests.put(
        f"{API_BASE}/api/playback/tracks/0/times",
        json={
            "start_time": 15.0,
            "end_time": 90.0
        }
    )
    
    if response.status_code != 200:
        print(f"✗ Status: {response.status_code}")
        print(f"  Response: {response.text}")
        return False
    
    print(f"✓ Set track times successfully")
    
    # Verify the change
    response = requests.get(f"{API_BASE}/api/playback/tracks")
    tracks = response.json().get('tracks', [])
    
    if len(tracks) > 0:
        track = tracks[0]
        if track.get('start_time') == 15.0 and track.get('end_time') == 90.0:
            print(f"✓ Track times verified: {track.get('start_time')}s - {track.get('end_time')}s")
        else:
            print(f"✗ Track times not updated correctly")
            return False
    
    return True

def test_validation():
    """Test input validation"""
    print("\nTesting input validation...")
    
    # Test invalid start time (negative)
    response = requests.put(
        f"{API_BASE}/api/playback/tracks/0/times",
        json={"start_time": -10.0}
    )
    
    if response.status_code == 400:
        print("✓ Negative start time correctly rejected")
    else:
        print(f"✗ Should reject negative start time, got status {response.status_code}")
        return False
    
    # Test start >= end
    response = requests.put(
        f"{API_BASE}/api/playback/tracks/0/times",
        json={"start_time": 100.0, "end_time": 50.0}
    )
    
    if response.status_code == 400:
        print("✓ start_time >= end_time correctly rejected")
    else:
        print(f"✗ Should reject start >= end, got status {response.status_code}")
        return False
    
    return True

if __name__ == '__main__':
    print("\nCustom Track Times - Flask API Tests\n")
    print("=" * 60)
    
    # Check if server is running
    try:
        response = requests.get(f"{API_BASE}/api/playback/status", timeout=2)
    except requests.exceptions.RequestException as e:
        print(f"✗ Cannot connect to Flask server at {API_BASE}")
        print(f"  Please start the server with: cd backend && python app.py")
        sys.exit(1)
    
    all_passed = True
    
    if not test_status_endpoint():
        all_passed = False
    
    if not test_tracks_endpoint():
        all_passed = False
    
    if not test_set_track_times():
        all_passed = False
    
    if not test_validation():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ALL API TESTS PASSED")
        sys.exit(0)
    else:
        print("✗ SOME API TESTS FAILED")
        sys.exit(1)
