#!/usr/bin/env python3
"""
Ubuntu ISO Remastering Tool
Version: 0.00.3

Purpose: Downloads Ubuntu 24.04.2 Live Server ISO for remastering purposes.
Expectations: 
- Shows version number before any sudo prompts
- Downloads Ubuntu ISO with live progress display
- Always ends with ls -tralsh command
- Will be frequently edited with version increments
- Handles missing dependencies gracefully
- Auto-installs all required dependencies
"""

import os
import sys
import subprocess

def install_dependency(package_name, pip_name=None):
    """Install a Python package using pip3"""
    if pip_name is None:
        pip_name = package_name
    
    print(f"Installing {package_name}...")
    try:
        # Try to install using pip3
        result = subprocess.run([sys.executable, "-m", "pip", "install", pip_name, "-y"], 
                              capture_output=True, text=True, check=True)
        print(f"✓ {package_name} installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install {package_name}: {e}")
        return False

def check_and_install_dependencies():
    """Check and install all required dependencies"""
    print("Checking dependencies...")
    
    dependencies = [
        ("requests", "requests"),
        ("tqdm", "tqdm")
    ]
    
    for module_name, pip_name in dependencies:
        try:
            __import__(module_name)
            print(f"✓ {module_name} already installed")
        except ImportError:
            print(f"✗ {module_name} not found, installing...")
            if not install_dependency(module_name, pip_name):
                print(f"Failed to install {module_name}. Please install manually: pip3 install {pip_name}")
                return False
    
    print("All dependencies ready!")
    return True

def main():
    print("Ubuntu ISO Remastering Tool - Version 0.00.3")
    print("=" * 50)
    
    # Check and install dependencies
    if not check_and_install_dependencies():
        cleanup_and_exit()
    
    # Now import the dependencies
    try:
        import requests
        from tqdm import tqdm
    except ImportError as e:
        print(f"Critical error: {e}")
        cleanup_and_exit()
    
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