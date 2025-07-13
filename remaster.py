#!/usr/bin/env python3
"""
Ubuntu ISO Remastering Tool
Version: 0.00.1

Purpose: Downloads Ubuntu 24.04.2 Live Server ISO for remastering purposes.
Expectations: 
- Shows version number before any sudo prompts
- Downloads Ubuntu ISO with live progress display
- Always ends with ls -tralsh command
- Will be frequently edited with version increments
"""

import os
import sys
import requests
import subprocess
from tqdm import tqdm

def main():
    print("Ubuntu ISO Remastering Tool - Version 0.00.1")
    print("=" * 50)
    
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
        
        # Download with progress bar
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
        
        print(f"\nDownload completed: {filename}")
        
    except requests.exceptions.RequestException as e:
        print(f"Error downloading file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)
    
    # Always end with ls -tralsh
    print("\n" + "=" * 50)
    print("Directory listing:")
    subprocess.run(["ls", "-tralsh"])

if __name__ == "__main__":
    main()