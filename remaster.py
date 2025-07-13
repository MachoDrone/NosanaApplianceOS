#!/usr/bin/env python3
"""
Ubuntu ISO Remastering Tool
Version: 0.01.6

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

def inject_hello_files(work_dir, efi_img, mbr_img):
    opt_dir = os.path.join(work_dir, "opt")
    os.makedirs(opt_dir, exist_ok=True)
    with open(os.path.join(opt_dir, "HelloNOS.OPT"), "w") as f:
        f.write("Hello from HelloNOS.OPT!\n")
    with open(efi_img, "ab") as f:
        f.write(b"Hello from HelloNOS.ESP!\n")
    with open(mbr_img, "ab") as f:
        f.write(b"Hello from HelloNOS.BOOT!\n")
    print("Injected HelloNOS.ESP, HelloNOS.BOOT, HelloNOS.OPT test files.")

def verify_hello_files(new_iso):
    print("Verifying injected files in new ISO...")
    # 1. Check HelloNOS.OPT in opt dir
    opt_found = False
    try:
        os.makedirs("_iso_mount", exist_ok=True)
        run_command(f"sudo mount -o loop {new_iso} _iso_mount", "Mounting new ISO for verification", check=False)
        opt_path = os.path.join("_iso_mount", "opt", "HelloNOS.OPT")
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
        run_command("sudo umount _iso_mount", "Unmounting ISO after verification", check=False)
        shutil.rmtree("_iso_mount", ignore_errors=True)
    # 2. Check HelloNOS.ESP in ESP partition (using binwalk to extract EFI partition)
    esp_found = False
    try:
        os.makedirs("_iso_esp", exist_ok=True)
        run_command(f"binwalk --dd='.*' {new_iso} -C _iso_esp", "Extracting ESP partition with binwalk", check=False)
        for root, dirs, files in os.walk("_iso_esp"):
            for file in files:
                if file.endswith(".img") or file.endswith(".bin"):
                    try:
                        with open(os.path.join(root, file), "rb") as f:
                            if b"Hello from HelloNOS.ESP!" in f.read():
                                print("PASS: HelloNOS.ESP found in ESP partition of ISO.")
                                esp_found = True
                                break
                    except Exception:
                        continue
            if esp_found:
                break
        if not esp_found:
            print("FAIL: HelloNOS.ESP not found in ESP partition.")
    except Exception as e:
        print(f"FAIL: Error checking HelloNOS.ESP: {e}")
    finally:
        shutil.rmtree("_iso_esp", ignore_errors=True)
    # 3. Check HelloNOS.BOOT in MBR/BOOT area (first 1MB of ISO)
    boot_found = False
    try:
        with open(new_iso, "rb") as f:
            mbr_data = f.read(1024*1024)  # Read first 1MB
            if b"Hello from HelloNOS.BOOT!" in mbr_data:
                print("PASS: HelloNOS.BOOT found in MBR/BOOT area of ISO.")
                boot_found = True
        if not boot_found:
            print("FAIL: HelloNOS.BOOT not found in MBR/BOOT area.")
    except Exception as e:
        print(f"FAIL: Error checking HelloNOS.BOOT: {e}")

def remaster_ubuntu_2204(dc_disable_cleanup, inject_hello):
    import requests
    from tqdm import tqdm
    iso_url = "https://ubuntu.mirror.garr.it/releases/noble/ubuntu-24.04.2-live-server-amd64.iso"
    iso_name = "ubuntu-24.04.2-live-server-amd64.iso"
    new_iso = "NosanaAOS-0.24.04.2.iso"
    work_dir = os.path.abspath("work_2204")
    temp_paths = [work_dir, "boot_hybrid.img", "efi.img"]
    try:
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
            if not check_file_exists(iso_name):
                print(f"ERROR: Downloaded ISO is too small or invalid. Aborting remaster process.")
                if not dc_disable_cleanup:
                    cleanup(temp_paths)
                return
        else:
            print(f"Using existing ISO: {iso_name}")
        run_command(f"dd if={iso_name} bs=1 count=432 of=boot_hybrid.img", "Extracting MBR template (boot_hybrid.img)")
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
        run_command(f"dd if={iso_name} bs=512 skip={efi_start} count={efi_count} of=efi.img", "Extracting EFI partition (efi.img)")
        run_command(f"xorriso -osirrox on -indev {iso_name} -extract / {work_dir}", f"Extracting ISO file tree to {work_dir}")
        print("You can now customize the extracted ISO in:", work_dir)
        if inject_hello:
            inject_hello_files(work_dir, "efi.img", "boot_hybrid.img")
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
        if inject_hello:
            verify_hello_files(new_iso)
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
    print("Ubuntu ISO Remastering Tool - Version 0.01.6")
    print("=" * 50)
    dc_disable_cleanup = "-dc" in sys.argv
    inject_hello = "-hello" in sys.argv
    check_and_install_dependencies()
    remaster_ubuntu_2204(dc_disable_cleanup, inject_hello)
    print("\n" + "=" * 50)
    print("Directory listing:")
    subprocess.run(["ls", "-tralsh"])

if __name__ == "__main__":
    main()