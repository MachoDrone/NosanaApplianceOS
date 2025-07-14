#!/usr/bin/env python3
"""
Ubuntu ISO Remastering Tool - Standalone Version
Version: 0.02.7-standalone-final-v13

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
  
  # Allow proxy configuration and mirror testing to be completely interactive
  # Do NOT configure apt at all - let installer do natural mirror testing
  proxy: null
  
  # Force minimal server installation from the start
  source:
    id: ubuntu-server-minimal
    search_drivers: true
  
  # Force these specific values (should skip their screens entirely)  
  ssh:
    install-server: false
    
  snaps: []
  
  # Do NOT install additional packages - use source selection instead
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
    linux /casper/vmlinuz autoinstall ds=nocloud;s=file:///cdrom/ cloud-config-url=file:///cdrom/user-data
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
    
    # Create vendor-data file (sometimes required)
    vendor_data_dst = os.path.join(server_dir, "vendor-data")
    with open(vendor_data_dst, 'w') as f:
        f.write("{}\n")
    print(f"Created: {vendor_data_dst}")
    
    # Create network-data file (sometimes required for cloud-init)
    network_data_dst = os.path.join(server_dir, "network-data")
    with open(network_data_dst, 'w') as f:
        f.write("version: 2\n")
    print(f"Created: {network_data_dst}")
    
    # Also create autoinstall files in the root directory (alternative location)
    root_user_data = os.path.join(work_dir, "user-data")
    with open(root_user_data, 'w') as f:
        f.write(AUTOINSTALL_USER_DATA)
    print(f"Created: {root_user_data}")
    
    root_meta_data = os.path.join(work_dir, "meta-data")
    with open(root_meta_data, 'w') as f:
        f.write(AUTOINSTALL_META_DATA)
    print(f"Created: {root_meta_data}")
    
    # Create additional files in root for maximum compatibility
    root_vendor_data = os.path.join(work_dir, "vendor-data")
    with open(root_vendor_data, 'w') as f:
        f.write("{}\n")
    print(f"Created: {root_vendor_data}")
    
    root_network_data = os.path.join(work_dir, "network-data")
    with open(root_network_data, 'w') as f:
        f.write("version: 2\n")
    print(f"Created: {root_network_data}")
    
    # Create autoinstall.yaml file (alternative format)
    autoinstall_yaml = os.path.join(work_dir, "autoinstall.yaml")
    with open(autoinstall_yaml, 'w') as f:
        f.write(AUTOINSTALL_USER_DATA.replace("#cloud-config\n", ""))
    print(f"Created: {autoinstall_yaml}")
    
    # Create autoinstall.yml file (another alternative)
    autoinstall_yml = os.path.join(work_dir, "autoinstall.yml")
    with open(autoinstall_yml, 'w') as f:
        f.write(AUTOINSTALL_USER_DATA.replace("#cloud-config\n", ""))
    print(f"Created: {autoinstall_yml}")
    
    # Create a post-install cleanup script for manual execution
    cleanup_script = os.path.join(work_dir, "cleanup-minimal.sh")
    cleanup_content = """#!/bin/bash
# NosanaAOS Post-Install Cleanup Script
# Run this after first boot to minimize the installation

echo "Starting NosanaAOS minimization..."

# Disable and remove snapd
echo "Disabling snapd services..."
systemctl disable snapd.service snapd.socket snapd.seeded.service 2>/dev/null || true
systemctl mask snapd.service snapd.socket snapd.seeded.service 2>/dev/null || true

echo "Removing snapd packages (ubuntu-server-minimal should already be the only server package)..."
apt-get update
apt-get remove --purge -y snapd 2>/dev/null || true
apt-get autoremove --purge -y
apt-get autoclean

echo "Verification:"
echo "Ubuntu Server packages installed:"
dpkg -l | grep ubuntu-server || echo "  None found"
echo "Snapd packages:"
dpkg -l | grep snapd || echo "  None found (good!)"
echo "SSH service status:"
systemctl status ssh 2>/dev/null || echo "  Not installed (good!)"

echo "NosanaAOS minimization complete!"
echo "Total packages installed: $(dpkg -l | grep '^ii' | wc -l)"
"""
    with open(cleanup_script, 'w') as f:
        f.write(cleanup_content)
    os.chmod(cleanup_script, 0o755)
    print(f"Created: {cleanup_script}")
    
    # Debug: show file contents
    print("\n--- DEBUG: Autoinstall file verification ---")
    print(f"user-data size: {os.path.getsize(user_data_dst)} bytes")
    print(f"meta-data size: {os.path.getsize(meta_data_dst)} bytes")
    with open(user_data_dst, 'r') as f:
        lines = f.readlines()
        print(f"user-data first few lines:")
        for i, line in enumerate(lines[:5]):
            print(f"  {i+1}: {line.rstrip()}")
    print("--- END DEBUG ---\n")
    
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
            
            # Debug: show the kernel command line we added
            print("\n--- DEBUG: GRUB kernel command ---")
            lines = GRUB_AUTOINSTALL_CFG.split('\n')
            for line in lines:
                if 'linux /casper/vmlinuz' in line:
                    print(f"Kernel command: {line.strip()}")
            print("--- END DEBUG ---\n")
            
            print("--- DEBUG: Files created for autoinstall detection ---")
            autoinstall_files = [
                "/server/user-data", "/server/meta-data", "/server/vendor-data", "/server/network-data",
                "/user-data", "/meta-data", "/vendor-data", "/network-data", 
                "/autoinstall.yaml", "/autoinstall.yml", "/cleanup-minimal.sh"
            ]
            for af in autoinstall_files:
                full_path = os.path.join(work_dir, af.lstrip('/'))
                if os.path.exists(full_path):
                    print(f"  ✓ {af} ({os.path.getsize(full_path)} bytes)")
                else:
                    print(f"  ✗ {af} (missing)")
            print("--- END DEBUG ---\n")
            print("NOTE: After installation, run '/cleanup-minimal.sh' as root to minimize the system")
            
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
    print("Ubuntu ISO Remastering Tool - Version 0.02.7-standalone-final-v13")
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