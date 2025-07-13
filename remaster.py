#!/usr/bin/env python3
"""
Ubuntu ISO Remastering Tool
Version: 0.00.5

Purpose: Downloads Ubuntu 24.04.2 Live Server ISO for remastering purposes.
Expectations: 
- Shows version number before any sudo prompts
- Downloads Ubuntu ISO with live progress display
- Always ends with ls -tralsh command
- Will be frequently edited with version increments
- Handles missing dependencies gracefully
- Auto-installs all required dependencies with no user interaction
"""

import os
import sys
import subprocess

def run_command(cmd, description=""):
    """Run a command and return success status"""
    if description:
        print(f"{description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed: {e}")
        return False

def install_system_dependencies():
    """Install system-level dependencies"""
    print("Installing system dependencies...")
    
    # Update package list
    if not run_command("sudo apt-get update", "Updating package list"):
        return False
    
    # Install python3-pip if not available
    if not run_command("sudo apt-get install -y python3-pip", "Installing python3-pip"):
        return False
    
    print("✓ System dependencies installed")
    return True

def install_python_dependency(package_name):
    """Install a Python package using multiple methods"""
    print(f"Installing {package_name}...")
    
    # Method 1: Try pip3 install
    if run_command(f"pip3 install {package_name}", f"Installing {package_name} (pip3)"):
        print(f"✓ {package_name} installed successfully")
        return True
    
    # Method 2: Try pip install
    if run_command(f"pip install {package_name}", f"Installing {package_name} (pip)"):
        print(f"✓ {package_name} installed successfully")
        return True
    
    # Method 3: Try with --user flag
    if run_command(f"pip3 install --user {package_name}", f"Installing {package_name} (user)"):
        print(f"✓ {package_name} installed successfully")
        return True
    
    # Method 4: Try with sudo
    if run_command(f"sudo pip3 install {package_name}", f"Installing {package_name} (sudo pip3)"):
        print(f"✓ {package_name} installed successfully")
        return True
    
    # Method 5: Try apt-get for Python packages
    apt_package_map = {
        "requests": "python3-requests",
        "tqdm": "python3-tqdm"
    }
    
    if package_name in apt_package_map:
        apt_package = apt_package_map[package_name]
        if run_command(f"sudo apt-get install -y {apt_package}", f"Installing {package_name} (apt-get)"):
            print(f"✓ {package_name} installed successfully via apt-get")
            return True
    
    # Method 6: Try with python3 -m pip
    if run_command(f"python3 -m pip install {package_name}", f"Installing {package_name} (python3 -m pip)"):
        print(f"✓ {package_name} installed successfully")
        return True
    
    # Method 7: Try with python3 -m pip --user
    if run_command(f"python3 -m pip install --user {package_name}", f"Installing {package_name} (python3 -m pip --user)"):
        print(f"✓ {package_name} installed successfully")
        return True
    
    print(f"✗ All installation methods failed for {package_name}")
    return False

def check_and_install_dependencies():
    """Check and install all required dependencies"""
    print("Checking dependencies...")
    
    # First ensure system dependencies are available
    if not install_system_dependencies():
        return False
    
    dependencies = ["requests", "tqdm"]
    
    for module_name in dependencies:
        try:
            __import__(module_name)
            print(f"✓ {module_name} already installed")
        except ImportError:
            print(f"✗ {module_name} not found, installing...")
            if not install_python_dependency(module_name):
                print(f"CRITICAL: All installation methods failed for {module_name}")
                print("Attempting emergency installation...")
                
                # Emergency method: Try to install via apt-get with force
                apt_package_map = {
                    "requests": "python3-requests",
                    "tqdm": "python3-tqdm"
                }
                
                if module_name in apt_package_map:
                    apt_package = apt_package_map[module_name]
                    if not run_command(f"sudo apt-get install -y --force-yes {apt_package}", f"Emergency install {module_name}"):
                        print(f"EMERGENCY INSTALLATION FAILED for {module_name}")
                        return False
                else:
                    return False
    
    print("All dependencies ready!")
    return True

def main():
    print("Ubuntu ISO Remastering Tool - Version 0.00.5")
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