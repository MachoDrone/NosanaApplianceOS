#!/bin/bash
# verify_hellonos.sh

echo "Checking for HelloNOS files after installation..."

echo "1. Checking EFI partition for HelloNOS.ESP:"
if [ -d "/boot/efi" ]; then
    echo "EFI partition mounted at /boot/efi"
    # Extract bytes at offset 1024 to check for HelloNOS.ESP
    sudo dd if=/dev/sda1 bs=1 skip=1024 count=10 2>/dev/null | hexdump -C
else
    echo "EFI partition not found"
fi

echo -e "\n2. Checking MBR area for HelloNOS.BOOT:"
# Extract bytes at offset 512 to check for HelloNOS.BOOT
sudo dd if=/dev/sda bs=1 skip=512 count=10 2>/dev/null | hexdump -C

echo -e "\n3. Checking /opt for HelloNOS.OPT:"
if [ -f "/opt/HelloNOS.OPT" ]; then
    echo "Found HelloNOS.OPT in /opt"
    cat /opt/HelloNOS.OPT
else
    echo "HelloNOS.OPT not found in /opt (expected - this file doesn't persist)"
fi
