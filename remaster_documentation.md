# Remaster.py Documentation

## Purpose
`remaster.py` is a Python script designed for downloading and remastering Ubuntu ISOs (22.04.2+, hybrid MBR+EFI). The script provides a complete workflow for downloading, extracting, modifying, and rebuilding Ubuntu ISOs with hybrid boot support.

## Current Version: 0.02.6

## Core Expectations
1. **Version Display**: Always displays the current version number before any sudo password prompts
2. **ISO Download**: Downloads Ubuntu 24.04.2 Live Server ISO from the specified mirror
3. **Live Progress**: Shows real-time download progress regardless of file size
4. **ISO Remastering**: Complete ISO extraction, modification, and rebuilding with hybrid MBR+EFI support
5. **Consistent Ending**: Always concludes with `ls -tralsh` command to show directory contents
6. **Frequent Updates**: Designed to be edited frequently with version increments
7. **Graceful Error Handling**: Handles missing dependencies and crashes with cleanup
8. **Auto-Dependency Management**: Automatically checks and installs all required dependencies with no user interaction
9. **Aggressive Installation**: Uses multiple installation methods to ensure success
10. **Smart Download**: Skips download if ISO file already exists
11. **Temp File Management**: All temp files are in the current directory with optional cleanup control
12. **Test File Injection**: Optional HelloNOS test file injection for EFI/MBR testing

## Current Features
- Downloads Ubuntu 24.04.2 Live Server AMD64 ISO
- Live progress bar using tqdm library
- Complete ISO extraction using xorriso
- MBR template extraction (432 bytes for --grub2-mbr)
- EFI partition extraction with automatic sector detection
- Hybrid ISO building with proper GPT structure
- Optional HelloNOS test file injection (-hello argument)
- Optional cleanup disable (-dc argument)
- Automatic system dependency installation
- Multiple Python package installation methods
- File existence check to avoid redundant downloads
- Error handling for network issues
- Automatic directory listing at completion
- Crash cleanup with proper unmounting
- Version tracking in script header
- Works on minimal Ubuntu Server installations

## Arguments
- **No arguments**: Standard remastering without test files
- **-hello**: Inject HelloNOS test files (ESP, BOOT, OPT) and verify them
- **-dc**: Disable cleanup (keep temp files for debugging)

## Dependencies (Auto-Installed)
### System Dependencies
- Python 3
- python3-pip (auto-installed via apt-get)
- xorriso (auto-installed via apt-get)
- coreutils (dd command, auto-installed via apt-get)
- binwalk (auto-installed via apt-get)

### Python Dependencies
- requests library (auto-installed via pip)
- tqdm library (auto-installed via pip)

## HelloNOS Test Files (with -hello argument)
When using `-hello`, the script injects and verifies three test files:

1. **HelloNOS.ESP**: Injected at offset 1024 in EFI partition (tests EFI area modification)
2. **HelloNOS.BOOT**: Injected at offset 512 in MBR area (tests MBR/boot area modification)
3. **HelloNOS.OPT**: Placed in /opt directory of ISO (tests filesystem modification, live environment only)

**Note**: HelloNOS.OPT does NOT persist after installation - it only exists in the live environment.

## Installation Methods Used
The script tries multiple installation methods for maximum compatibility:
1. **pip3 install package_name**
2. **pip install package_name**
3. **pip3 install --user package_name**
4. **sudo pip3 install package_name**
5. **python3 -m pip install package_name**
6. **python3 -m pip install --user package_name**

## Download Information
- **URL**: https://ubuntu.mirror.garr.it/releases/noble/ubuntu-24.04.2-live-server-amd64.iso
- **Filename**: ubuntu-24.04.2-live-server-amd64.iso
- **Size**: ~3.0 GB
- **Smart Download**: Checks if file exists before downloading

## Output
- **Remastered ISO**: NosanaAOS-0.24.04.2.iso
- **Temp Files**: boot_hybrid.img, efi.img, working_dir/ (removed unless -dc used)

## Usage
```bash
# Standard remastering
python3 remaster.py

# With HelloNOS test files
python3 remaster.py -hello

# Keep temp files for debugging
python3 remaster.py -dc

# Both options combined
python3 remaster.py -hello -dc
```

## Ubuntu 22.04+ Compatibility
The script handles Ubuntu 22.04+ changes:
- Uses GPT partitioning instead of MBR-only
- Proper EFI partition extraction with fdisk detection
- Modern xorriso commands with --grub2-mbr
- Hybrid boot support with -append_partition

## xorriso Command Used
```bash
xorriso -as mkisofs -r -V 'NosanaAOS' -o NosanaAOS-0.24.04.2.iso \
  --grub2-mbr boot_hybrid.img -partition_offset 16 --mbr-force-bootable \
  -append_partition 2 28732ac11ff8d211ba4b00a0c93ec93b efi.img \
  -appended_part_as_gpt -iso_mbr_part_type a2a0d0ebe5b9334487c068b6b72699c7 \
  -c '/boot.catalog' -b '/boot/grub/i386-pc/eltorito.img' \
  -no-emul-boot -boot-load-size 4 -boot-info-table --grub2-boot-info \
  -eltorito-alt-boot -e '--interval:appended_partition_2:::' -no-emul-boot working_dir
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
- **0.00.5**: Aggressive dependency installation with 7 methods and emergency fallback
- **0.00.6**: Added file existence check and updated download URL
- **0.02.6**: Complete remastering functionality with xorriso, EFI/MBR extraction, HelloNOS test files, hybrid ISO building

## File Location
- Main script: `remaster.py`
- Documentation: `remaster_documentation.md`
- Verification script: `VerifyRemaster.sh`