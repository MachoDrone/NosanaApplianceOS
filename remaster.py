#!/usr/bin/env python3
"""
Ubuntu ISO Remastering Tool
Version: 0.00.9

Purpose: Downloads and remasters Ubuntu ISOs (22.04.2+, hybrid MBR+EFI, and more in future). All temp files are in the current directory. Use -dc to disable cleanup.
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
    run_command("sudo apt-get install -y python3-pip xorriso coreutils", "Installing python3-pip, xorriso, coreutils (dd)")
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
            print(f"✗ {module} not found, installing...")
            if not install_python_dependency(module):
                print(f"CRITICAL: Could not install {module}")
                sys.exit(1)
    print("All dependencies ready!")

def check_file_exists(filename, min_size_mb=100):
    if os.path.exists(filename) and os.path.getsize(filename) > min_size_mb * 1024 * 1024:
        size_gb = os.path.getsize(filename) / (1024**3)
        print(f"✓ ISO file already exists: {filename} ({size_gb:.2f} GB)")
        return True
    return False

def cleanup(temp_paths):
    for path in temp_paths:
        if os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)
        elif os.path.isfile(path):
            try:
                os.remove(path)
            except Exception:
                pass

def remaster_ubuntu_2204(dc_disable_cleanup):
    import requests
    from tqdm import tqdm
    # ISO and output names
    iso_url = "https://releases.ubuntu.com/22.04/ubuntu-22.04.2-desktop-amd64.iso"
    iso_name = "ubuntu-22.04.2-desktop-amd64.iso"
    new_iso = "NosanaAOS-0.24.04.2.iso"
    work_dir = os.path.abspath("work_2204")
    os.makedirs(work_dir, exist_ok=True)
    temp_paths = [work_dir, "boot_hybrid.img", "efi.img", iso_name]
    try:
        # Download ISO if needed
        if not check_file_exists(iso_name):
            print(f"Downloading: {iso_url}")
            r = requests.get(iso_url, stream=True)
            if r.status_code != 200:
                print(f"ERROR: Failed to download ISO. HTTP status code: {r.status_code}")
                print("Aborting remaster process.")
                if not dc_disable_cleanup:
                    cleanup(temp_paths)
                return
            total = int(r.headers.get('content-length', 0))
            with open(iso_name, 'wb') as f, tqdm(desc=iso_name, total=total, unit='iB', unit_scale=True) as pbar:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
            print(f"Download completed: {iso_name}")
            # Check file size after download
            if not check_file_exists(iso_name):
                print(f"ERROR: Downloaded ISO is too small or invalid. Aborting remaster process.")
                if not dc_disable_cleanup:
                    cleanup(temp_paths)
                return
        else:
            print(f"Using existing ISO: {iso_name}")

        # Extract MBR template
        run_command(f"dd if={iso_name} bs=1 count=432 of=boot_hybrid.img", "Extracting MBR template (boot_hybrid.img)")
        # Find EFI partition start and size
        try:
            fdisk_out = subprocess.check_output(f"fdisk -l {iso_name}", shell=True, text=True)
            efi_line = next(l for l in fdisk_out.splitlines() if 'EFI System' in l)
            parts = efi_line.split()
            efi_start, efi_end = int(parts[1]), int(parts[2])
            efi_count = efi_end - efi_start + 1
        except Exception as e:
            print(f"ERROR: Could not parse EFI partition from fdisk output: {e}")
            print("Aborting remaster process.")
            if not dc_disable_cleanup:
                cleanup(temp_paths)
            return
        # Extract EFI partition
        run_command(f"dd if={iso_name} bs=512 skip={efi_start} count={efi_count} of=efi.img", "Extracting EFI partition (efi.img)")
        # Extract ISO file tree
        run_command(f"xorriso -osirrox on -indev {iso_name} -extract / {work_dir}", f"Extracting ISO file tree to {work_dir}")
        print("You can now customize the extracted ISO in:", work_dir)
        # (Customization placeholder)
        # Rebuild ISO
        xorriso_cmd = (
            f"xorriso -as mkisofs -r "
            f"-V 'NosanaAOS 0.24.04.2 (EFIBIOS)' "
            f"-o {new_iso} "
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
        run_command(xorriso_cmd, f"Rebuilding ISO as {new_iso}")
        print(f"ISO remaster complete: {new_iso}")
        # Cleanup
        if not dc_disable_cleanup:
            print("Cleaning up temp files...")
            cleanup(temp_paths)
        else:
            print("-dc set: Not cleaning up temp files.")
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        if not dc_disable_cleanup:
            cleanup(temp_paths)

def main():
    print("Ubuntu ISO Remastering Tool - Version 0.00.9")
    print("=" * 50)
    dc_disable_cleanup = "-dc" in sys.argv
    check_and_install_dependencies()
    remaster_ubuntu_2204(dc_disable_cleanup)
    print("\n" + "=" * 50)
    print("Directory listing:")
    subprocess.run(["ls", "-tralsh"])

if __name__ == "__main__":
    main()