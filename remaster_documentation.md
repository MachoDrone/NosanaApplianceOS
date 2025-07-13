# Remaster.py Documentation

## Purpose
`remaster.py` is a Python script designed for downloading and preparing Ubuntu ISO files for remastering purposes. The script provides a streamlined workflow for obtaining Ubuntu Live Server ISOs with live download progress monitoring.

## Current Version: 0.00.4

## Core Expectations
1. **Version Display**: Always displays the current version number before any sudo password prompts
2. **ISO Download**: Downloads Ubuntu 24.04.2 Live Server ISO from the specified mirror
3. **Live Progress**: Shows real-time download progress regardless of file size
4. **Consistent Ending**: Always concludes with `ls -tralsh` command to show directory contents
5. **Frequent Updates**: Designed to be edited frequently with version increments
6. **Graceful Error Handling**: Handles missing dependencies and crashes with cleanup
7. **Auto-Dependency Management**: Automatically checks and installs all required dependencies
8. **System Package Management**: Uses apt-get for system dependencies and pip for Python packages

## Current Features
- Downloads Ubuntu 24.04.2 Live Server AMD64 ISO
- Live progress bar using tqdm library
- Automatic system dependency installation (python3-pip)
- Automatic Python package installation (requests, tqdm)
- Multiple installation fallback methods
- Error handling for network issues
- Automatic directory listing at completion
- Crash cleanup with sudo -k and ls -tralsh
- Version tracking in script header
- Works on minimal Ubuntu Server installations

## Dependencies (Auto-Installed)
- Python 3
- python3-pip (auto-installed via apt-get)
- requests library (auto-installed via pip)
- tqdm library (auto-installed via pip)

## Installation Methods Used
1. **System packages**: `sudo apt-get install -y python3-pip`
2. **Python packages**: `pip3 install package_name`
3. **Fallback methods**: `pip install`, `pip3 install --user`

## Usage
```bash
python3 remaster.py
```

## Remote Execution
```bash
wget -O - https://raw.githubusercontent.com/MachoDrone/NosanaApplianceOS/cursor/create-remaster-py-with-version-control-5dde/remaster.py | python3
```

## Evolution Tracking
This document will be updated as `remaster.py` evolves to include:
- New features added
- Version changes
- Modified expectations
- Additional dependencies
- Usage changes

## Version History
- **0.00.1**: Initial version with tqdm progress bar
- **0.00.2**: Added graceful tqdm handling, crash cleanup with sudo -k
- **0.00.3**: Added automatic dependency checking and installation
- **0.00.4**: Improved dependency installation with system package management and fallback methods

## File Location
- Main script: `remaster.py`
- Documentation: `remaster_documentation.md`