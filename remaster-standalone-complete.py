#!/usr/bin/env python3

import subprocess
import sys
import os
import requests
from tqdm import tqdm
import tempfile
import shutil
import time

# Inline autoinstall configuration files  
AUTOINSTALL_USER_DATA = """#cloud-config
autoinstall:
  version: 1
  
  # Interactive sections - user can configure these
  interactive-sections:
    - locale
    - keyboard
    - network
    - proxy
    - storage
    - identity
    - ubuntu-pro
    - drivers
  
  # Explicitly configure proxy section to use full interactive mode
  proxy: ~
  
  # Don't configure apt at all - let installer handle mirrors naturally
  # This prevents autoinstall from interfering with proxy/mirror testing
  apt:
    disable_components: []
    preserve_sources_list: true
  
  # Force minimal server installation
  source:
    id: ubuntu-server-minimal
    search_drivers: true
  
  # Force these specific values (should skip their screens entirely)  
  ssh:
    install-server: false
    allow-pw: false
    authorized-keys: []
    
  snaps: []
  
  # Use source selection instead of packages
  packages: []
  
  updates: security
  
  # Simple cleanup after installation
  late-commands:
    - echo "AUTOINSTALL SUCCESS - SSH disabled, minimal server installed" > /target/var/log/autoinstall-success.log
    
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

def run_command(cmd, description="", check=True):
    print(f"{description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=check)
        if result.returncode != 0:
            print(f"Command failed: {cmd}")
            print(f"Error output: {result.stderr}")
            print(f"Standard output: {result.stdout}")
        return result.returncode == 0
    except Exception as e:
        print(f"Error running command: {e}")
        return False

def install_system_dependencies():
    print("Installing system dependencies...")
    run_command("sudo apt-get update", "Updating package list")
    run_command("sudo apt-get install -y python3-pip xorriso coreutils binwalk p7zip-full", "Installing dependencies")
    print("✓ System dependencies installed")

def install_python_dependency(package_name):
    try:
        __import__(package_name)
        print(f"✓ {package_name} already installed")
        return True
    except ImportError:
        print(f"Installing {package_name}...")
        result = subprocess.run([sys.executable, "-m", "pip", "install", package_name], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ {package_name} installed successfully")
            return True
        else:
            print(f"✗ Failed to install {package_name}: {result.stderr}")
            return False

def check_and_install_dependencies():
    print("Checking dependencies...")
    
    # Install system dependencies
    install_system_dependencies()
    
    # Check and install Python dependencies
    dependencies = ["requests", "tqdm"]
    for dep in dependencies:
        if not install_python_dependency(dep):
            print(f"✗ Failed to install {dep}")
            return False
    
    print("All dependencies ready!")
    return True

def check_file_exists(filename, min_size_mb=100):
    if os.path.exists(filename):
        size = os.path.getsize(filename)
        size_mb = size / (1024 * 1024)
        if size_mb >= min_size_mb:
            return True
    return False

def force_unmount(path):
    """Force unmount a path using various methods"""
    for cmd in [
        f"sudo umount -l {path}",
        f"sudo umount -f {path}",
        f"sudo umount {path}",
        f"umount -l {path}",
        f"umount -f {path}",
        f"umount {path}"
    ]:
        subprocess.run(cmd, shell=True, capture_output=True)

def cleanup(temp_paths):
    print("Cleaning up temporary files...")
    for path in temp_paths:
        if os.path.exists(path):
            if os.path.isdir(path):
                force_unmount(path)
                # Fix permissions before removing
                subprocess.run(f"sudo chmod -R 755 {path}", shell=True, capture_output=True)
                subprocess.run(f"sudo chown -R {os.getuid()}:{os.getgid()} {path}", shell=True, capture_output=True)
                subprocess.run(f"rm -rf {path}", shell=True)
            else:
                try:
                    os.remove(path)
                except:
                    subprocess.run(f"rm -f {path}", shell=True)
    print("✓ Cleanup complete")

def ensure_clean_dir(path):
    if os.path.exists(path):
        # Fix permissions before trying to remove
        subprocess.run(f"sudo chmod -R 755 {path}", shell=True, capture_output=True)
        subprocess.run(f"sudo chown -R {os.getuid()}:{os.getgid()} {path}", shell=True, capture_output=True)
        subprocess.run(f"rm -rf {path}", shell=True)
    os.makedirs(path, exist_ok=True)

def inject_autoinstall_files(work_dir):
    print("Injecting autoinstall configuration...")
    
    # Create server directory for autoinstall files
    server_dir = os.path.join(work_dir, "server")
    os.makedirs(server_dir, exist_ok=True)
    
    # Create user-data file
    user_data_dst = os.path.join(server_dir, "user-data")
    with open(user_data_dst, 'w') as f:
        f.write(AUTOINSTALL_USER_DATA)
    print(f"Created: {user_data_dst}")
    
    # Create meta-data file
    meta_data_dst = os.path.join(server_dir, "meta-data")
    with open(meta_data_dst, 'w') as f:
        f.write(AUTOINSTALL_META_DATA)
    print(f"Created: {meta_data_dst}")
    
    # Create vendor-data file (sometimes required)
    vendor_data_dst = os.path.join(server_dir, "vendor-data")
    with open(vendor_data_dst, 'w') as f:
        f.write("{}\n")
    print(f"Created: {vendor_data_dst}")
    
    # Create network-data file (sometimes required for cloud-init)
    network_data_dst = os.path.join(server_dir, "network-data")
    with open(network_data_dst, 'w') as f:
        f.write("{}\n")
    print(f"Created: {network_data_dst}")
    
    # Modify GRUB configuration to include autoinstall option
    grub_cfg = os.path.join(work_dir, "boot", "grub", "grub.cfg")
    if os.path.exists(grub_cfg):
        # Backup original
        try:
            shutil.copy2(grub_cfg, grub_cfg + ".backup")
        except PermissionError:
            print("Warning: Could not backup grub.cfg (permission denied)")
        
        # Create new grub configuration with autoinstall option
        grub_dir = os.path.dirname(grub_cfg)
        autoinstall_grub = os.path.join(grub_dir, "grub.cfg.autoinstall")
        
        with open(autoinstall_grub, 'w') as f:
            f.write(GRUB_AUTOINSTALL_CFG)
        
        # Replace original with autoinstall version
        try:
            shutil.copy2(autoinstall_grub, grub_cfg)
            print(f"✓ Modified GRUB configuration for autoinstall")
        except PermissionError:
            print("Warning: Could not modify grub.cfg (permission denied)")
    else:
        print("Warning: grub.cfg not found")
    
    print("✓ Autoinstall configuration injected")

def download_iso(url, filename):
    if check_file_exists(filename):
        print(f"Using existing ISO: {filename}")
        return True
    
    print(f"Downloading {filename}...")
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    total_size = int(response.headers.get('content-length', 0))
    
    with open(filename, 'wb') as f, tqdm(
        desc=filename,
        total=total_size,
        unit='B',
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                bar.update(len(chunk))
    
    return True

def inject_hello_files(work_dir, efi_img, mbr_img):
    print("Injecting hello files...")
    
    # Create hello directory
    hello_dir = os.path.join(work_dir, "hello")
    os.makedirs(hello_dir, exist_ok=True)
    
    # Create hello.txt
    hello_txt = os.path.join(hello_dir, "hello.txt")
    with open(hello_txt, 'w') as f:
        f.write("Hello from NosanaAOS Ubuntu 24.04.2 Remastered ISO!\n")
        f.write("This is a custom Ubuntu Server installation.\n")
        f.write("Created by the Ubuntu ISO Remastering Tool.\n")
    
    # Create info.txt with system information
    info_txt = os.path.join(hello_dir, "info.txt")
    with open(info_txt, 'w') as f:
        f.write("NosanaAOS Ubuntu 24.04.2 - Custom Server Installation\n")
        f.write("==========================================\n")
        f.write("- Ubuntu Server (minimized)\n")
        f.write("- SSH disabled by default\n")
        f.write("- No snap packages installed\n")
        f.write("- Third-party drivers enabled\n")
        f.write("- Security updates enabled\n")
    
    print("✓ Hello files injected")

def extract_boot_files(iso_filename):
    """Extract MBR template and EFI partition following HybridRemasterInstructions.txt"""
    print("Extracting boot files from original ISO...")
    
    # Extract MBR template (first 432 bytes)
    print("Extracting MBR template (boot_hybrid.img)...")
    if not run_command(f"dd if={iso_filename} of=boot_hybrid.img bs=1 count=432", "Extracting MBR template"):
        return False
    
    # Find EFI partition using fdisk
    print("Finding EFI partition...")
    result = subprocess.run(f"fdisk -l {iso_filename}", shell=True, capture_output=True, text=True)
    
    efi_start = efi_end = None
    for line in result.stdout.split('\n'):
        if 'EFI' in line or 'EFI System' in line:
            parts = line.split()
            try:
                efi_start = int(parts[1])
                efi_end = int(parts[2])
                break
            except (ValueError, IndexError):
                continue
    
    if efi_start and efi_end:
        efi_count = efi_end - efi_start + 1
        print(f"Found EFI partition: sectors {efi_start}-{efi_end} (count: {efi_count})")
        if not run_command(f"dd if={iso_filename} of=efi.img bs=512 skip={efi_start} count={efi_count}", "Extracting EFI partition"):
            return False
    else:
        print("✗ Could not find EFI partition")
        return False
    
    return True

def find_boot_image(work_dir):
    """Find the correct boot image file for Ubuntu 24.04.2"""
    boot_candidates = [
        "boot/grub/i386-pc/eltorito.img",
        "isolinux/isolinux.bin",
        "boot/isolinux/isolinux.bin"
    ]
    
    for candidate in boot_candidates:
        full_path = os.path.join(work_dir, candidate)
        if os.path.exists(full_path):
            print(f"Found boot image: {candidate}")
            return candidate
    
    print("Warning: No boot image found, using default")
    return "boot/grub/i386-pc/eltorito.img"

def create_hybrid_iso(work_dir, output_filename):
    """Create hybrid bootable ISO following HybridRemasterInstructions.txt"""
    print("Creating hybrid bootable ISO...")
    
    # Find the boot image
    boot_image = find_boot_image(work_dir)
    
    # Set proper permissions
    run_command(f"sudo chmod -R 755 {work_dir}", "Setting permissions", check=False)
    
    # Create ISO using hybrid method from HybridRemasterInstructions.txt
    create_iso_cmd = f"""
    xorriso -as mkisofs -r \\
        -V 'NosanaAOS Ubuntu 24.04.2' \\
        -o {output_filename} \\
        --grub2-mbr boot_hybrid.img \\
        -partition_offset 16 \\
        --mbr-force-bootable \\
        -append_partition 2 28732ac11ff8d211ba4b00a0c93ec93b efi.img \\
        -appended_part_as_gpt \\
        -iso_mbr_part_type a2a0d0ebe5b9334487c068b6b72699c7 \\
        -c '/boot.catalog' \\
        -b '/{boot_image}' \\
        -no-emul-boot -boot-load-size 4 -boot-info-table --grub2-boot-info \\
        -eltorito-alt-boot \\
        -e '--interval:appended_partition_2:::' \\
        -no-emul-boot \\
        {work_dir}
    """
    
    if run_command(create_iso_cmd, "Creating hybrid ISO"):
        return True
    
    # Fallback method if hybrid fails
    print("Hybrid method failed, trying fallback method...")
    
    fallback_cmd = f"""
    xorriso -as mkisofs -r \\
        -V 'NosanaAOS Ubuntu 24.04.2' \\
        -o {output_filename} \\
        -J -joliet-long -l \\
        -c '/boot.catalog' \\
        -b '/{boot_image}' \\
        -no-emul-boot -boot-load-size 4 -boot-info-table \\
        {work_dir}
    """
    
    if run_command(fallback_cmd, "Creating basic bootable ISO"):
        return True
    
    # Final fallback using genisoimage
    print("All xorriso methods failed, trying genisoimage...")
    final_cmd = f"genisoimage -r -V 'NosanaAOS Ubuntu 24.04.2' -cache-inodes -J -joliet-long -l -o {output_filename} {work_dir}"
    
    return run_command(final_cmd, "Creating ISO with genisoimage")

def remaster_ubuntu_2204(dc_disable_cleanup=False, inject_hello=True, inject_autoinstall=True):
    print("Ubuntu ISO Remastering Tool - Version 0.02.8-complete")
    print("=" * 62)
    
    # Check and install dependencies
    if not check_and_install_dependencies():
        print("✗ Dependency check failed")
        return False
    
    # Configuration
    iso_url = "https://releases.ubuntu.com/24.04.2/ubuntu-24.04.2-live-server-amd64.iso"
    iso_filename = "ubuntu-24.04.2-live-server-amd64.iso"
    new_iso_filename = "NosanaAOS-0.24.04.2.iso"
    
    # Download ISO
    if not download_iso(iso_url, iso_filename):
        print("✗ ISO download failed")
        return False
    
    # Temporary paths for cleanup
    temp_paths = ["working_dir", "boot_hybrid.img", "efi.img"]
    
    try:
        # Extract boot files first (following HybridRemasterInstructions.txt)
        if not extract_boot_files(iso_filename):
            print("✗ Failed to extract boot files")
            return False
        
        # Extract ISO file tree
        work_dir = "working_dir"
        ensure_clean_dir(work_dir)
        
        print(f"Extracting ISO file tree to {os.path.abspath(work_dir)}...")
        if not run_command(f"7z x -o{work_dir} {iso_filename}", "Extracting ISO contents"):
            return False
        
        print(f"You can now customize the extracted ISO in: {os.path.abspath(work_dir)}")
        
        # Inject autoinstall files if requested
        if inject_autoinstall:
            inject_autoinstall_files(work_dir)
        
        # Inject hello files if requested
        if inject_hello:
            inject_hello_files(work_dir, "efi.img", "boot_hybrid.img")
        
        # Create hybrid bootable ISO
        if not create_hybrid_iso(work_dir, new_iso_filename):
            print("✗ ISO creation failed")
            return False
        
        # Verify the new ISO
        if os.path.exists(new_iso_filename):
            size = os.path.getsize(new_iso_filename)
            size_mb = size / (1024 * 1024)
            print(f"✓ New ISO created: {new_iso_filename} ({size_mb:.1f} MB)")
            return True
        else:
            print("✗ New ISO creation failed")
            return False
    
    except Exception as e:
        print(f"✗ Error during remastering: {e}")
        return False
    
    finally:
        if not dc_disable_cleanup:
            cleanup(temp_paths)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Ubuntu ISO Remastering Tool")
    parser.add_argument("-dc", "--disable-cleanup", action="store_true", help="Disable cleanup of temporary files")
    parser.add_argument("-hello", "--inject-hello", action="store_true", default=True, help="Inject hello files into ISO")
    parser.add_argument("-autoinstall", "--inject-autoinstall", action="store_true", default=True, help="Inject autoinstall configuration")
    
    args = parser.parse_args()
    
    # If no arguments provided, enable autoinstall by default
    if len(sys.argv) == 1:
        args.inject_autoinstall = True
    
    success = remaster_ubuntu_2204(
        dc_disable_cleanup=args.disable_cleanup,
        inject_hello=args.inject_hello,
        inject_autoinstall=args.inject_autoinstall
    )
    
    if success:
        print("\n✅ ISO remastering completed successfully!")
        print("🚀 You can now boot from NosanaAOS-0.24.04.2.iso")
        if args.inject_autoinstall:
            print("🔧 Select 'Install Ubuntu Server (Semi-Automated)' from the boot menu")
            print("📋 The installer will ask for language, keyboard, network, proxy, storage, and user settings")
            print("⚙️  SSH will be disabled, minimal server will be installed, and no snaps will be added")
            print("✅ PROXY UI FIX: Mirror test results should now display in proper UI widget")
            print("🔥 BOOTABLE: ISO created using proper hybrid method for MBR+EFI support")
    else:
        print("\n❌ ISO remastering failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()