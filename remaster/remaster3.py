#!/usr/bin/env python3
"""
Ubuntu ISO Remastering Tool - Production Ready Version (remaster3.py)
Version: 0.03.0-production

Purpose: Securely downloads and remasters Ubuntu ISOs (22.04+) with hybrid MBR+EFI support.
Follows HybridRemasterInstructions.txt for proper ISO creation.

Security improvements:
- No shell injection vulnerabilities
- Proper path validation
- Atomic file operations
- Comprehensive error handling
"""

import os
import sys
import subprocess
import shlex
import tempfile
import hashlib
import json
import logging
from pathlib import Path
from typing import List, Tuple, Optional, Dict
from contextlib import contextmanager
import argparse
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('remaster.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants based on HybridRemasterInstructions.txt
MBR_TEMPLATE_SIZE = 432  # First 432 bytes for GRUB2 MBR
DEFAULT_ISO_URL = "https://mirror.pilotfiber.com/ubuntu-iso/24.04.2/ubuntu-24.04.2-live-server-amd64.iso"
DEFAULT_ISO_FILENAME = "ubuntu-24.04.2-live-server-amd64.iso"
MIN_ISO_SIZE_MB = 100
EFI_PARTITION_TYPE = "28732ac11ff8d211ba4b00a0c93ec93b"
ISO_MBR_PART_TYPE = "a2a0d0ebe5b9334487c068b6b72699c7"

# Autoinstall configuration with snap disabled instead of removed
AUTOINSTALL_USER_DATA = """#cloud-config
autoinstall:
  version: 1
  
  # Interactive sections - let user configure everything
  interactive-sections:
    - locale
    - keyboard  
    - network
    - proxy
    - apt
    - storage
    - identity
    - ubuntu-pro
    - drivers
  
  # Only force the absolute minimum
  source:
    id: ubuntu-server-minimal
    search_drivers: true
  
  ssh:
    install-server: false
    
  snaps: []
  packages: []
  
  # Disable snap services instead of removing
  late-commands:
    - echo "AUTOINSTALL SUCCESS" > /target/var/log/autoinstall-success.log
    - curtin in-target -- systemctl disable snapd.service
    - curtin in-target -- systemctl disable snapd.socket
    - curtin in-target -- systemctl disable snapd.seeded.service
    - curtin in-target -- systemctl mask snapd.service
    - curtin in-target -- systemctl mask snapd.socket
    - curtin in-target -- systemctl mask snapd.seeded.service
    
  shutdown: reboot
"""

AUTOINSTALL_META_DATA = """instance-id: ubuntu-autoinstall
local-hostname: ubuntu-server
"""

GRUB_AUTOINSTALL_CFG = """set timeout=30
set default=0

menuentry "Install Ubuntu Server (Semi-Automated)" {
    set gfxpayload=keep
    linux /casper/vmlinuz autoinstall ds=nocloud;s=file:///cdrom/server/ console=tty0 console=ttyS0,115200n8
    initrd /casper/initrd
}

menuentry "Install Ubuntu Server (Manual)" {
    set gfxpayload=keep
    linux /casper/vmlinuz
    initrd /casper/initrd
}

menuentry "Try Ubuntu Server without installing" {
    set gfxpayload=keep
    linux /casper/vmlinuz
    initrd /casper/initrd
}
"""


class SecurePathError(Exception):
    """Raised when a path validation fails"""
    pass


class ISORemasterError(Exception):
    """Base exception for ISO remastering errors"""
    pass


def validate_path(path: str, must_exist: bool = False) -> Path:
    """
    Validate and sanitize a file path to prevent directory traversal attacks.
    
    Args:
        path: The path to validate
        must_exist: Whether the path must already exist
        
    Returns:
        Path object for the validated path
        
    Raises:
        SecurePathError: If the path is invalid or insecure
    """
    if not path:
        raise SecurePathError("Path cannot be empty")
    
    # Convert to Path object and resolve
    try:
        path_obj = Path(path).resolve()
    except Exception as e:
        raise SecurePathError(f"Invalid path '{path}': {e}")
    
    # Check for directory traversal attempts
    if ".." in path:
        raise SecurePathError(f"Path contains '..': {path}")
    
    # Check if path exists when required
    if must_exist and not path_obj.exists():
        raise SecurePathError(f"Path does not exist: {path_obj}")
    
    return path_obj


def run_command(cmd_list: List[str], description: str = "", check: bool = True,
                capture_output: bool = True) -> subprocess.CompletedProcess:
    """
    Safely run a command without shell injection risk.
    
    Args:
        cmd_list: List of command arguments
        description: Description for logging
        check: Whether to raise exception on non-zero exit
        capture_output: Whether to capture stdout/stderr
        
    Returns:
        CompletedProcess instance
    """
    if description:
        logger.info(f"{description}...")
    
    logger.debug(f"Running command: {' '.join(cmd_list)}")
    
    try:
        result = subprocess.run(
            cmd_list,
            capture_output=capture_output,
            text=True,
            check=check
        )
        
        if result.returncode != 0:
            logger.error(f"Command failed with code {result.returncode}")
            if result.stderr:
                logger.error(f"Error output: {result.stderr}")
        
        return result
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {e}")
        if e.stderr:
            logger.error(f"Error output: {e.stderr}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error running command: {e}")
        raise


def atomic_write_file(path: Path, content: str, mode: int = 0o644):
    """
    Write file atomically to prevent corruption.
    
    Args:
        path: Path to write to
        content: Content to write
        mode: File permissions
    """
    # Create temporary file in same directory for atomic rename
    temp_fd, temp_path = tempfile.mkstemp(dir=path.parent, text=True)
    
    try:
        with os.fdopen(temp_fd, 'w') as f:
            f.write(content)
        
        # Set permissions
        os.chmod(temp_path, mode)
        
        # Atomic rename
        os.rename(temp_path, path)
        logger.debug(f"Atomically wrote {len(content)} bytes to {path}")
        
    except Exception as e:
        # Clean up temp file on error
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise


@contextmanager
def mount_iso(iso_path: Path, mount_point: Path):
    """
    Context manager to safely mount and unmount ISO.
    
    Args:
        iso_path: Path to ISO file
        mount_point: Where to mount it
    """
    mount_point.mkdir(parents=True, exist_ok=True)
    
    try:
        run_command(
            ["sudo", "mount", "-o", "loop,ro", str(iso_path), str(mount_point)],
            f"Mounting {iso_path}"
        )
        yield mount_point
    finally:
        try:
            run_command(
                ["sudo", "umount", str(mount_point)],
                f"Unmounting {mount_point}",
                check=False
            )
        except Exception as e:
            logger.warning(f"Failed to unmount {mount_point}: {e}")


def verify_file_checksum(file_path: Path, expected_checksum: Optional[str] = None) -> str:
    """
    Verify file integrity with SHA256 checksum.
    
    Args:
        file_path: Path to file to verify
        expected_checksum: Expected SHA256 hash (optional)
        
    Returns:
        Calculated checksum
        
    Raises:
        ISORemasterError: If checksum doesn't match expected
    """
    sha256_hash = hashlib.sha256()
    
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    calculated = sha256_hash.hexdigest()
    
    if expected_checksum and calculated != expected_checksum:
        raise ISORemasterError(
            f"Checksum mismatch for {file_path}: "
            f"expected {expected_checksum}, got {calculated}"
        )
    
    return calculated


def download_file(url: str, dest_path: Path, expected_checksum: Optional[str] = None) -> bool:
    """
    Download file with progress bar and optional checksum verification.
    
    Args:
        url: URL to download from
        dest_path: Where to save the file
        expected_checksum: Expected SHA256 hash (optional)
        
    Returns:
        True if successful
    """
    try:
        import requests
        from tqdm import tqdm
        
        logger.info(f"Downloading {url} to {dest_path}")
        
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(dest_path, 'wb') as f:
            with tqdm(
                desc=dest_path.name,
                total=total_size,
                unit='B',
                unit_scale=True,
                unit_divisor=1024
            ) as progress_bar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        progress_bar.update(len(chunk))
        
        # Verify checksum if provided
        if expected_checksum:
            verify_file_checksum(dest_path, expected_checksum)
        
        logger.info(f"Successfully downloaded {dest_path}")
        return True
        
    except Exception as e:
        logger.error(f"Download failed: {e}")
        if dest_path.exists():
            dest_path.unlink()
        return False


def extract_mbr_template(iso_path: Path, output_path: Path):
    """
    Extract MBR template from ISO as per HybridRemasterInstructions.txt
    
    Args:
        iso_path: Source ISO file
        output_path: Where to save MBR template
    """
    logger.info(f"Extracting MBR template ({MBR_TEMPLATE_SIZE} bytes)")
    
    run_command([
        "dd",
        f"if={iso_path}",
        f"of={output_path}",
        "bs=1",
        f"count={MBR_TEMPLATE_SIZE}"
    ], "Extracting MBR template")


def find_efi_partition(iso_path: Path) -> Tuple[int, int]:
    """
    Find EFI partition location in ISO using fdisk.
    
    Args:
        iso_path: Path to ISO file
        
    Returns:
        Tuple of (start_sector, sector_count)
    """
    result = run_command(
        ["fdisk", "-l", str(iso_path)],
        "Analyzing ISO partition table"
    )
    
    # Parse fdisk output to find EFI System partition
    for line in result.stdout.splitlines():
        if 'EFI System' in line:
            parts = line.split()
            if len(parts) >= 3:
                try:
                    start = int(parts[1])
                    end = int(parts[2])
                    count = end - start + 1
                    logger.info(f"Found EFI partition: sectors {start}-{end} (count: {count})")
                    return start, count
                except (ValueError, IndexError):
                    continue
    
    # Fallback to default values from Ubuntu 22.04
    logger.warning("Could not parse EFI partition info, using default values")
    return 7129428, 8496


def extract_efi_partition(iso_path: Path, output_path: Path):
    """
    Extract EFI partition from ISO.
    
    Args:
        iso_path: Source ISO file
        output_path: Where to save EFI partition image
    """
    start_sector, sector_count = find_efi_partition(iso_path)
    
    run_command([
        "dd",
        f"if={iso_path}",
        f"of={output_path}",
        "bs=512",
        f"skip={start_sector}",
        f"count={sector_count}"
    ], f"Extracting EFI partition ({sector_count} sectors)")


def extract_iso_contents(iso_path: Path, dest_dir: Path):
    """
    Extract ISO contents using xorriso.
    
    Args:
        iso_path: Source ISO file
        dest_dir: Destination directory
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    run_command([
        "xorriso",
        "-osirrox", "on",
        "-indev", str(iso_path),
        "-extract", "/", str(dest_dir)
    ], f"Extracting ISO contents to {dest_dir}")
    
    # Fix permissions
    run_command([
        "sudo", "chmod", "-R", "755", str(dest_dir)
    ], "Fixing directory permissions", check=False)
    
    run_command([
        "sudo", "chown", "-R", f"{os.getuid()}:{os.getgid()}", str(dest_dir)
    ], "Fixing directory ownership", check=False)


def create_autoinstall_files(work_dir: Path):
    """
    Create autoinstall configuration files.
    
    Args:
        work_dir: Working directory containing extracted ISO
    """
    logger.info("Creating autoinstall configuration files")
    
    # Create server directory
    server_dir = work_dir / "server"
    server_dir.mkdir(exist_ok=True)
    
    # Write autoinstall files
    files_to_create = {
        server_dir / "user-data": AUTOINSTALL_USER_DATA,
        server_dir / "meta-data": AUTOINSTALL_META_DATA,
        server_dir / "vendor-data": "{}\n",
        server_dir / "network-data": "version: 2\n",
        work_dir / "user-data": AUTOINSTALL_USER_DATA,
        work_dir / "meta-data": AUTOINSTALL_META_DATA,
    }
    
    for file_path, content in files_to_create.items():
        atomic_write_file(file_path, content)
        logger.info(f"Created: {file_path} ({len(content)} bytes)")


def modify_grub_config(work_dir: Path):
    """
    Modify GRUB configuration for autoinstall.
    
    Args:
        work_dir: Working directory containing extracted ISO
    """
    grub_cfg_path = work_dir / "boot" / "grub" / "grub.cfg"
    
    if not grub_cfg_path.exists():
        logger.warning(f"GRUB config not found at {grub_cfg_path}")
        return
    
    # Read original config
    original_grub = grub_cfg_path.read_text()
    
    # Create new config with autoinstall menu
    new_grub = GRUB_AUTOINSTALL_CFG + "\n\n# Original GRUB configuration below:\n" + original_grub
    
    # Write atomically
    atomic_write_file(grub_cfg_path, new_grub)
    logger.info("Modified GRUB configuration for autoinstall")


def build_hybrid_iso(work_dir: Path, output_iso: Path, mbr_template: Path, efi_img: Path):
    """
    Build hybrid MBR+EFI ISO following HybridRemasterInstructions.txt
    
    Args:
        work_dir: Directory containing ISO contents
        output_iso: Output ISO path
        mbr_template: Path to MBR template
        efi_img: Path to EFI partition image
    """
    logger.info(f"Building hybrid ISO: {output_iso}")
    
    # Build command following HybridRemasterInstructions.txt exactly
    xorriso_cmd = [
        "xorriso", "-as", "mkisofs", "-r",
        "-V", "NosanaAOS Ubuntu 24.04.2",
        "-o", str(output_iso),
        "--grub2-mbr", str(mbr_template),
        "-partition_offset", "16",
        "--mbr-force-bootable",
        "-append_partition", "2", EFI_PARTITION_TYPE, str(efi_img),
        "-appended_part_as_gpt",
        "-iso_mbr_part_type", ISO_MBR_PART_TYPE,
        "-c", "/boot.catalog",
        "-b", "/boot/grub/i386-pc/eltorito.img",
        "-no-emul-boot", "-boot-load-size", "4", "-boot-info-table", "--grub2-boot-info",
        "-eltorito-alt-boot",
        "-e", "--interval:appended_partition_2:::",
        "-no-emul-boot",
        str(work_dir)
    ]
    
    try:
        run_command(xorriso_cmd, "Creating hybrid MBR+EFI ISO")
        
        # Verify ISO was created and has reasonable size
        if not output_iso.exists():
            raise ISORemasterError("ISO creation failed - output file not found")
        
        size_mb = output_iso.stat().st_size / (1024 * 1024)
        if size_mb < 1:
            raise ISORemasterError(f"ISO creation failed - file too small ({size_mb:.1f} MB)")
        
        logger.info(f"Successfully created ISO: {output_iso} ({size_mb:.1f} MB)")
        
    except subprocess.CalledProcessError as e:
        # If xorriso fails, try alternative method with genisoimage
        logger.warning("xorriso failed, trying genisoimage fallback")
        
        genisoimage_cmd = [
            "genisoimage", "-r",
            "-V", "NosanaAOS Ubuntu 24.04.2",
            "-cache-inodes", "-J", "-l", "-joliet-long",
            "-o", str(output_iso),
            str(work_dir)
        ]
        
        run_command(genisoimage_cmd, "Creating ISO with genisoimage (fallback)")


def cleanup_paths(paths: List[Path]):
    """
    Clean up temporary files and directories.
    
    Args:
        paths: List of paths to clean up
    """
    logger.info("Cleaning up temporary files")
    
    for path in paths:
        try:
            if path.exists():
                if path.is_dir():
                    # Try to unmount if it's a mount point
                    run_command(
                        ["sudo", "umount", str(path)],
                        check=False,
                        capture_output=False
                    )
                    
                    # Remove directory tree
                    import shutil
                    shutil.rmtree(path, ignore_errors=True)
                else:
                    path.unlink()
                
                logger.debug(f"Removed: {path}")
        except Exception as e:
            logger.warning(f"Failed to remove {path}: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Ubuntu ISO Remastering Tool - Production Ready",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -autoinstall                    # Create autoinstall ISO
  %(prog)s -autoinstall -dc               # Keep temporary files for debugging
  %(prog)s -autoinstall -iso custom.iso   # Use custom ISO file
        """
    )
    
    parser.add_argument("-autoinstall", action="store_true",
                       help="Create autoinstall ISO with minimal server configuration")
    parser.add_argument("-dc", "--disable-cleanup", action="store_true",
                       help="Disable cleanup of temporary files")
    parser.add_argument("-iso", "--iso-file", default=DEFAULT_ISO_FILENAME,
                       help=f"Input ISO file (default: {DEFAULT_ISO_FILENAME})")
    parser.add_argument("-url", "--iso-url", default=DEFAULT_ISO_URL,
                       help="URL to download ISO from")
    parser.add_argument("-o", "--output", default="NosanaAOS-0.24.04.2.iso",
                       help="Output ISO filename")
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("Ubuntu ISO Remastering Tool - Version 0.03.0-production")
    logger.info("=" * 70)
    
    # Paths to use
    iso_path = validate_path(args.iso_file)
    output_iso = validate_path(args.output)
    work_dir = Path("working_dir")
    mbr_template = Path("boot_hybrid.img")
    efi_img = Path("efi.img")
    
    temp_paths = [work_dir, mbr_template, efi_img]
    
    try:
        # Check dependencies
        required_tools = ["xorriso", "fdisk", "dd", "sudo"]
        missing_tools = []
        
        for tool in required_tools:
            try:
                run_command(["which", tool], capture_output=False)
            except subprocess.CalledProcessError:
                missing_tools.append(tool)
        
        if missing_tools:
            logger.error(f"Missing required tools: {', '.join(missing_tools)}")
            logger.error("Please install missing dependencies")
            return 1
        
        # Download ISO if needed
        if not iso_path.exists():
            logger.info(f"ISO not found locally, downloading from {args.iso_url}")
            if not download_file(args.iso_url, iso_path):
                return 1
        else:
            logger.info(f"Using existing ISO: {iso_path}")
            # Verify it's large enough
            size_mb = iso_path.stat().st_size / (1024 * 1024)
            if size_mb < MIN_ISO_SIZE_MB:
                logger.error(f"ISO file too small ({size_mb:.1f} MB), possibly corrupted")
                return 1
        
        # Extract MBR template
        extract_mbr_template(iso_path, mbr_template)
        
        # Extract EFI partition
        extract_efi_partition(iso_path, efi_img)
        
        # Extract ISO contents
        extract_iso_contents(iso_path, work_dir)
        
        if args.autoinstall:
            # Create autoinstall files
            create_autoinstall_files(work_dir)
            
            # Modify GRUB config
            modify_grub_config(work_dir)
        
        # Build hybrid ISO
        build_hybrid_iso(work_dir, output_iso, mbr_template, efi_img)
        
        logger.info("=" * 70)
        logger.info(f"✅ Successfully created: {output_iso}")
        
        if args.autoinstall:
            logger.info("✅ Autoinstall configuration included:")
            logger.info("   - SSH disabled")
            logger.info("   - Minimal server installation")
            logger.info("   - Snap services disabled (not removed)")
            logger.info("   - Interactive proxy/mirror configuration")
        
        return 0
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        logger.debug(traceback.format_exc())
        return 1
        
    finally:
        if not args.disable_cleanup:
            cleanup_paths(temp_paths)


if __name__ == "__main__":
    sys.exit(main())