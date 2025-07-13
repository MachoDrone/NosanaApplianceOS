#!/usr/bin/env python3
"""
Ubuntu ISO Remastering Tool
Version: 0.02.3

Purpose: Downloads and remasters Ubuntu ISOs (22.04.2+, hybrid MBR+EFI, and more in future). All temp files are in the current directory. Use -dc to disable cleanup. Use -hello to inject and verify test files.
"""

import os
import sys
import subprocess
import shutil

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
    if os.path.isfile(filename):
        size_mb = os.path.getsize(filename) / (1024*1024)
        if size_mb >= min_size_mb:
            size_gb = size_mb / 1024
            print(f"✓ ISO file already exists: {filename} ({size_gb:.2f} GB)")
            return True
    return False

def force_unmount(path):
    """Force unmount a directory with multiple attempts"""
    if not os.path.exists(path):
        return True
    
    # Check if it's actually mounted
    try:
        result = subprocess.run(["mountpoint", "-q", path], capture_output=True)
        if result.returncode != 0:
            return True  # Not mounted
    except:
        pass
    
    print(f"Unmounting {path}...")
    # Try regular unmount first
    for attempt in range(3):
        result = subprocess.run(["sudo", "umount", path], capture_output=True)
        if result.returncode == 0:
            return True
        if attempt < 2:
            subprocess.run(["sleep", "1"])
    
    # Try force unmount
    result = subprocess.run(["sudo", "umount", "-f", path], capture_output=True)
    if result.returncode == 0:
        return True
    
    # Try lazy unmount as last resort
    result = subprocess.run(["sudo", "umount", "-l", path], capture_output=True)
    return result.returncode == 0

def cleanup(temp_paths):
    for path in temp_paths:
        if os.path.isdir(path):
            # Force unmount if it's a mount point
            force_unmount(path)
            
            try:
                shutil.rmtree(path, ignore_errors=True)
            except Exception:
                pass
            if os.path.isdir(path):
                print(f"shutil.rmtree failed for {path}, trying sudo rm -rf")
                subprocess.run(["sudo", "rm", "-rf", path])
            if os.path.isdir(path):
                print(f"ERROR: Could not remove directory {path} after all attempts.")
        elif os.path.isfile(path):
            try:
                os.remove(path)
            except Exception:
                pass

def ensure_clean_dir(path):
    if os.path.exists(path):
        force_unmount(path)
        subprocess.run(["sudo", "rm", "-rf", path])
    os.makedirs(path, exist_ok=True)
    subprocess.run(["sudo", "chown", f"{os.getuid()}:{os.getgid()}", path])

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
    print("Verifying injected files in new ISO...")
    opt_found = False
    mount_point = "_iso_mount"
    
    # Force cleanup any existing mount point first
    force_unmount(mount_point)
    if os.path.exists(mount_point):
        subprocess.run(["sudo", "rm", "-rf", mount_point], check=False)
    
    try:
        os.makedirs(mount_point, exist_ok=True)
        subprocess.run(["sudo", "chown", f"{os.getuid()}:{os.getgid()}", mount_point])
        
        # Try to mount, but handle case where it might already be mounted
        mount_result = subprocess.run(["sudo", "mount", "-o", "loop", new_iso, mount_point], 
                                    capture_output=True, text=True)
        
        if mount_result.returncode != 0 and "already mounted" in mount_result.stderr:
            print("ISO already mounted, continuing with verification...")
        elif mount_result.returncode != 0:
            print(f"Failed to mount ISO: {mount_result.stderr}")
            return
        else:
            print("Mounting new ISO for verification...")
            
        opt_path = os.path.join(mount_point, "opt", "HelloNOS.OPT")
        if os.path.isfile(opt_path):
            with open(opt_path, "r") as f:
                content = f.read()
                if "Hello from HelloNOS.OPT!" in content:
                    print("PASS: HelloNOS.OPT found in opt dir of ISO.")
                    opt_found = True
        if not opt_found:
            print("FAIL: HelloNOS.OPT not found or content mismatch.")
    except Exception as e:
        print(f"FAIL: Error checking HelloNOS.OPT: {e}")
    finally:
        # Ensure proper unmount
        force_unmount(mount_point)
        
        # Clean up mount point directory
        if os.path.exists(mount_point):
            subprocess.run(["sudo", "rm", "-rf", mount_point], check=False)
    
    # Check ESP partition by reading the ISO directly
    esp_found = False
    try:
        fdisk_out = subprocess.check_output(f"fdisk -l {new_iso}", shell=True, text=True)
        efi_line = next(l for l in fdisk_out.splitlines() if 'EFI System' in l)
        parts = efi_line.split()
        efi_start, efi_end = int(parts[1]), int(parts[2])
        with open(new_iso, "rb") as f:
            f.seek(efi_start * 512)
            efi_data = f.read((efi_end - efi_start + 1) * 512)
            if b"Hello from HelloNOS.ESP!" in efi_data:
                print("PASS: HelloNOS.ESP found in ESP partition of ISO.")
                esp_found = True
        if not esp_found:
            print("FAIL: HelloNOS.ESP not found in ESP partition.")
    except Exception as e:
        print(f"FAIL: Error checking HelloNOS.ESP: {e}")
    
    boot_found = False
    try:
        with open(new_iso, "rb") as f:
            mbr_data = f.read(1024*1024)
            if b"Hello from HelloNOS.BOOT!" in mbr_data:
                print("PASS: HelloNOS.BOOT found in MBR/BOOT area of ISO.")
                boot_found = True
        if not boot_found:
            print("FAIL: HelloNOS.BOOT not found in MBR/BOOT area.")
    except Exception as e:
        print(f"FAIL: Error checking HelloNOS.BOOT: {e}")

def remaster_ubuntu_2204(dc_disable_cleanup, inject_hello):
    iso_url = "https://ubuntu.mirror.garr.it/releases/noble/ubuntu-24.04.2-live-server-amd64.iso"
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
    run_command(f"dd if={iso_filename} of=boot_hybrid.img bs=1M count=1", "Extracting MBR template")
    
    print("Extracting EFI partition (efi.img)...")
    run_command(f"dd if={iso_filename} of=efi.img bs=512 skip=6608 count=11264", "Extracting EFI partition")
    
    work_dir = "working_dir"
    ensure_clean_dir(work_dir)
    print(f"Extracting ISO file tree to {os.path.abspath(work_dir)}...")
    run_command(f"xorriso -osirrox on -indev {iso_filename} -extract / {work_dir}", "Extracting ISO contents")
    
    print(f"You can now customize the extracted ISO in: {os.path.abspath(work_dir)}")
    
    if inject_hello:
        inject_hello_files(work_dir, "efi.img", "boot_hybrid.img")
    
    new_iso = "NosanaAOS-0.24.04.2.iso"
    print(f"Rebuilding ISO as {new_iso}...")
    
    # Check if boot files exist and build xorriso command accordingly
    eltorito_path = os.path.join(work_dir, "boot", "grub", "i386-pc", "eltorito.img")
    efi_boot_path = os.path.join(work_dir, "EFI", "boot", "bootx64.efi")
    
    if os.path.exists(eltorito_path) and os.path.exists(efi_boot_path):
        # Full hybrid boot with both BIOS and EFI
        xorriso_cmd = (
            f"xorriso -as mkisofs -r -V 'NosanaAOS' -o {new_iso} "
            f"-J -l -c boot.catalog "
            f"-b boot/grub/i386-pc/eltorito.img -no-emul-boot -boot-load-size 4 -boot-info-table "
            f"-eltorito-alt-boot -e EFI/boot/bootx64.efi -no-emul-boot "
            f"-append_partition 2 0xef efi.img "
            f"-partition_cyl_align all "
            f"-isohybrid-mbr boot_hybrid.img "
            f"-isohybrid-gpt-basdat "
            f"{work_dir}"
        )
    elif os.path.exists(eltorito_path):
        # BIOS boot only
        xorriso_cmd = (
            f"xorriso -as mkisofs -r -V 'NosanaAOS' -o {new_iso} "
            f"-J -l -c boot.catalog "
            f"-b boot/grub/i386-pc/eltorito.img -no-emul-boot -boot-load-size 4 -boot-info-table "
            f"-isohybrid-mbr boot_hybrid.img "
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
    print("Ubuntu ISO Remastering Tool - Version 0.02.3")
    print("==================================================")
    
    if not check_and_install_dependencies():
        return 1
    
    dc_disable_cleanup = "-dc" in sys.argv
    inject_hello = "-hello" in sys.argv
    
    if not remaster_ubuntu_2204(dc_disable_cleanup, inject_hello):
        return 1
    
    print("\n==================================================")
    print("Directory listing:")
    run_command("ls -tralsh", "Final directory listing")
    return 0

if __name__ == "__main__":
    sys.exit(main())