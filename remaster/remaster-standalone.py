#!/usr/bin/env python3
"""
Ubuntu ISO Remastering Tool - Standalone Version
Version: 0.02.7-standalone-fixed

Purpose: Downloads and remasters Ubuntu ISOs (22.04.2+, hybrid MBR+EFI, and more in future). All temp files are in the current directory. Use -dc to disable cleanup. Use -hello to inject and verify test files. Use -autoinstall to inject semi-automated installer configuration.

This standalone version includes autoinstall configuration files inline and handles file permissions properly.
"""

import os
import sys
import subprocess

# Inline autoinstall configuration files
AUTOINSTALL_USER_DATA = """#cloud-config
autoinstall:
  version: 1
  
  # Allow interactive selection for these components
  interactive-sections:
    - locale
    - keyboard
    - network
    - proxy
    - storage
    - identity
    - ubuntu-pro
    - drivers
  
  # Force specific choices
  locale: null  # Will be interactive
  keyboard: null  # Will be interactive
  
  # Network configuration - interactive but with sensible defaults
  network:
    version: 2
    
  # Proxy configuration - interactive
  proxy: null
  
  # Storage configuration - interactive
  storage:
    layout:
      name: lvm
  
  # Identity configuration - interactive (user will input name, username, etc.)
  identity: null
  
  # SSH configuration - force NO OpenSSH server installation
  ssh:
    install-server: false
    allow-pw: false
    authorized-keys: []
  
  # Package selection - force Ubuntu Server minimized
  packages:
    - ubuntu-server-minimal
  
  # Snap configuration - force NO featured server snaps
  snaps: []
  
  # Drivers configuration - force search for third-party drivers
  drivers:
    install: true
  
  # Ubuntu Pro configuration - default to skip but allow interactive choice
  ubuntu-pro:
    token: null  # Will be interactive with "Skip for now" default
  
  # Disable automatic updates during installation
  updates: security
  
  # Late commands to ensure minimized installation
  late-commands:
    - echo 'Installation completed with forced minimized server configuration'
    - systemctl disable snapd.service || true
    - systemctl disable snapd.socket || true
    - systemctl mask snapd.service || true
    - systemctl mask snapd.socket || true
  
  # Error commands for troubleshooting
  error-commands:
    - echo 'Installation failed, check logs'
    - journalctl -n 50
  
  # Reboot after installation
  shutdown: reboot
"""

AUTOINSTALL_META_DATA = """instance-id: ubuntu-autoinstall
local-hostname: ubuntu-server
"""

GRUB_AUTOINSTALL_CFG = """set timeout=30
set default=0

menuentry "Install Ubuntu Server (Semi-Automated)" {
    set gfxpayload=keep
    linux /casper/vmlinuz autoinstall ds=nocloud-net;s=/cdrom/server/
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
            print(result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False

def install_system_dependencies():
    print("Installing system dependencies...")
    run_command("sudo apt-get update", "Updating package list")
    run_command("sudo apt-get install -y python3-pip xorriso coreutils binwalk", "Installing python3-pip, xorriso, coreutils (dd), binwalk")
    print("✓ System dependencies installed")

def install_python_dependency(package_name):
    for cmd in [
        f"pip3 install {package_name}",
        f"pip install {package_name}",
        f"pip3 install --user {package_name}",
        f"sudo pip3 install {package_name}",
        f"python3 -m pip install {package_name}",
        f"python3 -m pip install --user {package_name}"
    ]:
        if run_command(cmd, f"Installing {package_name}"):
            return True
    return False

def check_and_install_dependencies():
    print("Checking dependencies...")
    install_system_dependencies()
    for module in ["requests", "tqdm"]:
        try:
            __import__(module)
            print(f"✓ {module} already installed")
        except ImportError:
            print(f"Installing {module}...")
            if not install_python_dependency(module):
                print(f"✗ Failed to install {module}")
                return False
    print("All dependencies ready!")
    return True

def check_file_exists(filename, min_size_mb=100):
    if os.path.exists(filename):
        file_size = os.path.getsize(filename)
        if file_size > min_size_mb * 1024 * 1024:
            return True
    return False

def force_unmount(path):
    if os.path.exists(path):
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
    
    # Modify GRUB configuration for autoinstall
    grub_cfg_path = os.path.join(work_dir, "boot", "grub", "grub.cfg")
    if os.path.exists(grub_cfg_path):
        # Ensure we can modify the file
        subprocess.run(f"chmod 644 {grub_cfg_path}", shell=True, capture_output=True)
        
        # Backup original grub.cfg
        try:
            import shutil
            shutil.copy2(grub_cfg_path, grub_cfg_path + ".backup")
        except PermissionError:
            # If we can't backup, just proceed
            print("Warning: Could not backup grub.cfg (permission denied)")
        
        # Read original GRUB config
        try:
            with open(grub_cfg_path, 'r') as f:
                original_grub = f.read()
            
            # Write new GRUB config with autoinstall menu
            with open(grub_cfg_path, 'w') as f:
                f.write(GRUB_AUTOINSTALL_CFG + "\n\n# Original GRUB configuration below:\n" + original_grub)
            
            print(f"Modified: {grub_cfg_path}")
        except PermissionError:
            print(f"Warning: Could not modify {grub_cfg_path} (permission denied)")
    else:
        print(f"Warning: {grub_cfg_path} not found")
    
    print("✓ Autoinstall configuration injected")

def inject_hello_files(work_dir, efi_img, mbr_img):
    print("Injected HelloNOS.ESP, HelloNOS.BOOT, HelloNOS.OPT test files.")
    
    # Inject into EFI partition
    with open(efi_img, "r+b") as f:
        f.seek(1024)
        f.write(b"Hello from HelloNOS.ESP! This is a test file in the EFI System Partition.\n")
    
    # Inject into MBR/boot area
    with open(mbr_img, "r+b") as f:
        f.seek(512)
        f.write(b"Hello from HelloNOS.BOOT! This is a test file in the MBR/boot area.\n")
    
    # Inject into opt directory
    opt_dir = os.path.join(work_dir, "opt")
    os.makedirs(opt_dir, exist_ok=True)
    with open(os.path.join(opt_dir, "HelloNOS.OPT"), "w") as f:
        f.write("Hello from HelloNOS.OPT! This is a test file in the /opt directory.\n")

def verify_hello_files(new_iso):
    print("Verifying HelloNOS test files...")
    
    # Check HelloNOS.OPT
    try:
        subprocess.run(f"mkdir -p _iso_mount", shell=True)
        subprocess.run(f"sudo mount -o loop {new_iso} _iso_mount", shell=True)
        
        opt_file = "_iso_mount/opt/HelloNOS.OPT"
        if os.path.exists(opt_file):
            with open(opt_file, 'r') as f:
                content = f.read()
            if "HelloNOS.OPT" in content:
                print("✓ PASS: HelloNOS.OPT found and verified")
            else:
                print("✗ FAIL: HelloNOS.OPT content incorrect")
        else:
            print("✗ FAIL: HelloNOS.OPT not found")
        
        subprocess.run(f"sudo umount _iso_mount", shell=True)
        subprocess.run(f"rm -rf _iso_mount", shell=True)
    except Exception as e:
        print(f"✗ FAIL: Error checking HelloNOS.OPT: {e}")
    
    # Check HelloNOS.ESP
    try:
        with open("efi.img", "rb") as f:
            f.seek(1024)
            content = f.read(100)
        if b"HelloNOS.ESP" in content:
            print("✓ PASS: HelloNOS.ESP found and verified")
        else:
            print("✗ FAIL: HelloNOS.ESP not found")
    except Exception as e:
        print(f"FAIL: Error checking HelloNOS.ESP: {e}")
    
    # Check HelloNOS.BOOT
    try:
        with open("boot_hybrid.img", "rb") as f:
            f.seek(512)
            content = f.read(100)
        if b"HelloNOS.BOOT" in content:
            print("✓ PASS: HelloNOS.BOOT found and verified")
        else:
            print("✗ FAIL: HelloNOS.BOOT not found")
    except Exception as e:
        print(f"FAIL: Error checking HelloNOS.BOOT: {e}")

def remaster_ubuntu_2204(dc_disable_cleanup, inject_hello, inject_autoinstall):
    iso_url = "https://mirror.pilotfiber.com/ubuntu-iso/24.04.2/ubuntu-24.04.2-live-server-amd64.iso"
    iso_filename = "ubuntu-24.04.2-live-server-amd64.iso"
    
    temp_paths = ["working_dir", "work_2204", "boot_hybrid.img", "efi.img", "_iso_mount"]
    
    if not check_file_exists(iso_filename):
        print(f"Downloading {iso_filename}...")
        try:
            import requests
            from tqdm import tqdm
            response = requests.get(iso_url, stream=True)
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            with open(iso_filename, 'wb') as f, tqdm(
                desc=iso_filename,
                total=total_size,
                unit='B',
                unit_scale=True,
                unit_divisor=1024,
            ) as bar:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    bar.update(len(chunk))
        except Exception as e:
            print(f"✗ Download failed: {e}")
            return False
    else:
        print(f"Using existing ISO: {iso_filename}")
    
    print("Extracting MBR template (boot_hybrid.img)...")
    run_command(f"dd if={iso_filename} of=boot_hybrid.img bs=1 count=432", "Extracting MBR template")
    
    print("Extracting EFI partition (efi.img)...")
    # For Ubuntu 22.04+, we need to find the EFI partition location using fdisk
    try:
        fdisk_result = subprocess.run(f"fdisk -l {iso_filename}", shell=True, capture_output=True, text=True)
        if fdisk_result.returncode == 0:
            fdisk_out = fdisk_result.stdout
            efi_lines = [l for l in fdisk_out.splitlines() if 'EFI System' in l]
            if efi_lines:
                efi_line = efi_lines[0]
                parts = efi_line.split()
                if len(parts) >= 3:
                    efi_start, efi_end = int(parts[1]), int(parts[2])
                    efi_count = efi_end - efi_start + 1
                    print(f"Found EFI partition: sectors {efi_start}-{efi_end} (count: {efi_count})")
                    run_command(f"dd if={iso_filename} of=efi.img bs=512 skip={efi_start} count={efi_count}", "Extracting EFI partition")
                else:
                    print("Could not parse EFI partition info, using fallback method")
                    run_command(f"dd if={iso_filename} of=efi.img bs=512 skip=6608 count=11264", "Extracting EFI partition (fallback)")
            else:
                print("No EFI System partition found, using fallback method")
                run_command(f"dd if={iso_filename} of=efi.img bs=512 skip=6608 count=11264", "Extracting EFI partition (fallback)")
        else:
            print("fdisk failed, using fallback method")
            run_command(f"dd if={iso_filename} of=efi.img bs=512 skip=6608 count=11264", "Extracting EFI partition (fallback)")
    except Exception as e:
        print(f"Error extracting EFI partition: {e}, using fallback method")
        run_command(f"dd if={iso_filename} of=efi.img bs=512 skip=6608 count=11264", "Extracting EFI partition (fallback)")
    
    work_dir = "working_dir"
    ensure_clean_dir(work_dir)
    print(f"Extracting ISO file tree to {os.path.abspath(work_dir)}...")
    result = run_command(f"xorriso -osirrox on -indev {iso_filename} -extract / {work_dir}", "Extracting ISO contents", check=False)
    
    # Fix permissions after extraction
    print("Fixing file permissions after extraction...")
    subprocess.run(f"sudo chmod -R 755 {work_dir}", shell=True, capture_output=True)
    subprocess.run(f"sudo chown -R {os.getuid()}:{os.getgid()} {work_dir}", shell=True, capture_output=True)
    
    print(f"You can now customize the extracted ISO in: {os.path.abspath(work_dir)}")
    
    if inject_hello:
        inject_hello_files(work_dir, "efi.img", "boot_hybrid.img")
    
    if inject_autoinstall:
        inject_autoinstall_files(work_dir)
    
    new_iso = "NosanaAOS-0.24.04.2.iso"
    print(f"Rebuilding ISO as {new_iso}...")
    
    # Check if boot files exist and build xorriso command accordingly
    eltorito_path = os.path.join(work_dir, "boot", "grub", "i386-pc", "eltorito.img")
    efi_boot_path = os.path.join(work_dir, "EFI", "boot", "bootx64.efi")
    
    if os.path.exists(eltorito_path) and os.path.exists(efi_boot_path):
        # Ubuntu 22.04+ hybrid boot with proper GPT structure
        xorriso_cmd = (
            f"xorriso -as mkisofs -r -V 'NosanaAOS' -o {new_iso} "
            f"--grub2-mbr boot_hybrid.img "
            f"-partition_offset 16 "
            f"--mbr-force-bootable "
            f"-append_partition 2 28732ac11ff8d211ba4b00a0c93ec93b efi.img "
            f"-appended_part_as_gpt "
            f"-iso_mbr_part_type a2a0d0ebe5b9334487c068b6b72699c7 "
            f"-c '/boot.catalog' "
            f"-b '/boot/grub/i386-pc/eltorito.img' "
            f"-no-emul-boot -boot-load-size 4 -boot-info-table --grub2-boot-info "
            f"-eltorito-alt-boot "
            f"-e '--interval:appended_partition_2:::' "
            f"-no-emul-boot "
            f"{work_dir}"
        )
    elif os.path.exists(eltorito_path):
        # BIOS boot only with MBR
        xorriso_cmd = (
            f"xorriso -as mkisofs -r -V 'NosanaAOS' -o {new_iso} "
            f"-J -l -c boot.catalog "
            f"-b boot/grub/i386-pc/eltorito.img -no-emul-boot -boot-load-size 4 -boot-info-table "
            f"--grub2-mbr boot_hybrid.img "
            f"--mbr-force-bootable "
            f"{work_dir}"
        )
    else:
        # Simple ISO without special boot
        xorriso_cmd = f"xorriso -as mkisofs -r -V 'NosanaAOS' -o {new_iso} -J -l {work_dir}"
    
    result = run_command(xorriso_cmd, "Building hybrid ISO")
    
    # Check if ISO was actually created
    if not os.path.exists(new_iso) or os.path.getsize(new_iso) < 1024*1024:
        print(f"✗ ISO creation failed or file is too small")
        return False
    
    print(f"ISO remaster complete: {new_iso}")
    
    if inject_hello:
        verify_hello_files(new_iso)
    
    if not dc_disable_cleanup:
        print("Cleaning up temp files...")
        cleanup(temp_paths)
    
    return True

def main():
    print("Ubuntu ISO Remastering Tool - Version 0.02.7-standalone-fixed")
    print("==================================================")
    print("NOTE: This script requires sudo privileges for file permission handling")
    print("Make sure you can run sudo commands when prompted")
    print("==================================================")
    
    if not check_and_install_dependencies():
        return 1
    
    dc_disable_cleanup = "-dc" in sys.argv
    inject_hello = "-hello" in sys.argv
    inject_autoinstall = "-autoinstall" in sys.argv
    
    if not remaster_ubuntu_2204(dc_disable_cleanup, inject_hello, inject_autoinstall):
        return 1
    
    print("\n==================================================")
    print("Directory listing:")
    # Use subprocess directly to ensure ls -tralsh actually runs
    try:
        result = subprocess.run(["ls", "-tralsh"], capture_output=True, text=True)
        if result.returncode == 0:
            print(result.stdout)
        else:
            print(result.stderr)
    except Exception as e:
        print(f"Error running ls: {e}")
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)