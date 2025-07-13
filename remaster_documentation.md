# Remaster.py Documentation

## Purpose
`remaster.py` is a Python script designed for downloading and preparing Ubuntu ISO files for remastering purposes. The script provides a streamlined workflow for obtaining Ubuntu Live Server ISOs with live download progress monitoring.

## Current Version: 0.00.1

## Core Expectations
1. **Version Display**: Always displays the current version number before any sudo password prompts
2. **ISO Download**: Downloads Ubuntu 24.04.2 Live Server ISO from the specified mirror
3. **Live Progress**: Shows real-time download progress regardless of file size
4. **Consistent Ending**: Always concludes with `ls -tralsh` command to show directory contents
5. **Frequent Updates**: Designed to be edited frequently with version increments

## Current Features
- Downloads Ubuntu 24.04.2 Live Server AMD64 ISO
- Live progress bar using tqdm library
- Error handling for network issues
- Automatic directory listing at completion
- Version tracking in script header

## Dependencies
- Python 3
- requests library
- tqdm library

## Usage
```bash
python3 remaster.py
```

## Evolution Tracking
This document will be updated as `remaster.py` evolves to include:
- New features added
- Version changes
- Modified expectations
- Additional dependencies
- Usage changes

## File Location
- Main script: `remaster.py`
- Documentation: `remaster_documentation.md`