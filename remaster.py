#!/usr/bin/env python3
"""
Ubuntu ISO Remastering Tool
Version: 0.00.2

Purpose: Downloads Ubuntu 24.04.2 Live Server ISO for remastering purposes.
Expectations: 
- Shows version number before any sudo prompts
- Downloads Ubuntu ISO with live progress display
- Always ends with ls -tralsh command
- Will be frequently edited with version increments
- Handles missing dependencies gracefully
"""

import os
import sys
import requests
import subprocess

def main():
    print("Ubuntu ISO Remastering Tool - Version 0.00.2")
    print("=" * 50)
    
    # Check for tqdm module
    try:
        from tqdm import tqdm
        has_tqdm = True
    except ImportError:
        has_tqdm = False
        print("Warning: tqdm module not found. Using basic progress display.")
        print("Install with: pip3 install tqdm")
        print()
    
    # Download URL
    url = "https://mirror.pilotfiber.com/ubuntu-iso/24.04.2/ubuntu-24.04.2-live-server-amd64.iso"
    filename = "ubuntu-24.04.2-live-server-amd64.iso"
    
    print(f"Downloading: {url}")
    print(f"Filename: {filename}")
    print()
    
    try:
        # Start download with progress bar
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Get total file size
        total_size = int(response.headers.get('content-length', 0))
        
        if has_tqdm:
            # Download with tqdm progress bar
            with open(filename, 'wb') as file, tqdm(
                desc=filename,
                total=total_size,
                unit='iB',
                unit_scale=True,
                unit_divisor=1024,
            ) as pbar:
                for data in response.iter_content(chunk_size=1024):
                    size = file.write(data)
                    pbar.update(size)
        else:
            # Download with basic progress display
            downloaded = 0
            with open(filename, 'wb') as file:
                for data in response.iter_content(chunk_size=1024):
                    size = file.write(data)
                    downloaded += size
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\rProgress: {downloaded}/{total_size} bytes ({percent:.1f}%)", end='', flush=True)
                    else:
                        print(f"\rDownloaded: {downloaded} bytes", end='', flush=True)
            print()  # New line after progress
        
        print(f"\nDownload completed: {filename}")
        
    except requests.exceptions.RequestException as e:
        print(f"Error downloading file: {e}")
        cleanup_and_exit()
    except Exception as e:
        print(f"Unexpected error: {e}")
        cleanup_and_exit()
    
    # Always end with ls -tralsh
    print("\n" + "=" * 50)
    print("Directory listing:")
    subprocess.run(["ls", "-tralsh"])

def cleanup_and_exit():
    """Clean up and exit with sudo -k and ls -tralsh"""
    print("\n" + "=" * 50)
    print("Script crashed. Running cleanup...")
    subprocess.run(["sudo", "-k"])
    print("Directory listing:")
    subprocess.run(["ls", "-tralsh"])
    sys.exit(1)

if __name__ == "__main__":
    main()