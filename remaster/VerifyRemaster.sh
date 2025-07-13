#!/bin/bash
# verify_hellonos.sh - Enhanced HelloNOS File Verification Script
# Version: 1.0
# Purpose: Verify the presence of HelloNOS test files after Ubuntu installation

echo "=============================================="
echo "HelloNOS File Verification Script v1.0"
echo "=============================================="
echo "Checking for HelloNOS files after installation..."
echo

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    if [ "$status" = "PASS" ]; then
        echo -e "\033[32m✓ PASS:\033[0m $message"
    elif [ "$status" = "FAIL" ]; then
        echo -e "\033[31m✗ FAIL:\033[0m $message"
    else
        echo -e "\033[33m! INFO:\033[0m $message"
    fi
}

# Function to detect the correct boot device
detect_boot_device() {
    local boot_device=""
    
    # Check common locations
    if [ -b "/dev/sda" ]; then
        boot_device="/dev/sda"
    elif [ -b "/dev/nvme0n1" ]; then
        boot_device="/dev/nvme0n1"
    elif [ -b "/dev/vda" ]; then
        boot_device="/dev/vda"
    else
        # Try to find from mount info
        boot_device=$(lsblk -no PKNAME $(findmnt -n -o SOURCE /) | head -1)
        if [ -n "$boot_device" ]; then
            boot_device="/dev/$boot_device"
        fi
    fi
    
    echo "$boot_device"
}

# Function to detect EFI partition
detect_efi_partition() {
    local boot_device=$1
    local efi_partition=""
    
    if [[ "$boot_device" == *"nvme"* ]]; then
        efi_partition="${boot_device}p1"
    else
        efi_partition="${boot_device}1"
    fi
    
    # Verify it's actually an EFI partition
    if [ -b "$efi_partition" ]; then
        local fstype=$(lsblk -no FSTYPE "$efi_partition" 2>/dev/null)
        if [ "$fstype" = "vfat" ]; then
            echo "$efi_partition"
        fi
    fi
}

echo "=== System Information ==="
BOOT_DEVICE=$(detect_boot_device)
if [ -n "$BOOT_DEVICE" ]; then
    print_status "INFO" "Boot device detected: $BOOT_DEVICE"
else
    print_status "FAIL" "Could not detect boot device"
    exit 1
fi

EFI_PARTITION=$(detect_efi_partition "$BOOT_DEVICE")
if [ -n "$EFI_PARTITION" ]; then
    print_status "INFO" "EFI partition detected: $EFI_PARTITION"
else
    print_status "INFO" "EFI partition not detected or not FAT32"
fi

echo

echo "=== Test 1: HelloNOS.ESP (EFI System Partition) ==="
if [ -d "/boot/efi" ]; then
    print_status "INFO" "EFI partition mounted at /boot/efi"
    
    if [ -n "$EFI_PARTITION" ]; then
        echo "Checking for HelloNOS.ESP at offset 1024 in $EFI_PARTITION:"
        
        # Extract more bytes to get the full message
        ESP_DATA=$(sudo dd if="$EFI_PARTITION" bs=1 skip=1024 count=50 2>/dev/null)
        if echo "$ESP_DATA" | grep -q "Hello from HelloNOS.ESP!"; then
            print_status "PASS" "HelloNOS.ESP found in EFI partition!"
            echo "Content preview:"
            echo "$ESP_DATA" | head -1
        else
            print_status "FAIL" "HelloNOS.ESP not found in EFI partition"
        fi
        
        # Show hex dump for verification
        echo "Hex dump of EFI partition at offset 1024:"
        sudo dd if="$EFI_PARTITION" bs=1 skip=1024 count=30 2>/dev/null | hexdump -C
    else
        print_status "FAIL" "Cannot check EFI partition - not detected"
    fi
else
    print_status "FAIL" "EFI partition not mounted at /boot/efi"
fi

echo

echo "=== Test 2: HelloNOS.BOOT (MBR/Boot Area) ==="
echo "Checking for HelloNOS.BOOT at offset 512 in $BOOT_DEVICE:"

# Extract more bytes to get the full message
BOOT_DATA=$(sudo dd if="$BOOT_DEVICE" bs=1 skip=512 count=50 2>/dev/null)
if echo "$BOOT_DATA" | grep -q "Hello from HelloNOS.BOOT!"; then
    print_status "PASS" "HelloNOS.BOOT found in MBR area!"
    echo "Content preview:"
    echo "$BOOT_DATA" | head -1
else
    print_status "FAIL" "HelloNOS.BOOT not found in MBR area"
fi

# Show hex dump for verification
echo "Hex dump of MBR area at offset 512:"
sudo dd if="$BOOT_DEVICE" bs=1 skip=512 count=30 2>/dev/null | hexdump -C

echo

echo "=== Test 3: HelloNOS.OPT (ISO Filesystem) ==="
if [ -f "/opt/HelloNOS.OPT" ]; then
    print_status "PASS" "HelloNOS.OPT found in /opt (unexpected!)"
    echo "Content:"
    cat /opt/HelloNOS.OPT
else
    print_status "INFO" "HelloNOS.OPT not found in /opt (expected - this file doesn't persist after installation)"
fi

echo

echo "=== Summary ==="
echo "Expected results after installation:"
echo "  • HelloNOS.ESP: Should be found in EFI partition"
echo "  • HelloNOS.BOOT: Should be found in MBR area"
echo "  • HelloNOS.OPT: Should NOT be found (live environment only)"
echo

echo "=== Additional Verification Commands ==="
echo "To manually verify the files, you can use:"
if [ -n "$EFI_PARTITION" ]; then
    echo "  EFI: sudo dd if=$EFI_PARTITION bs=1 skip=1024 count=25 | hexdump -C"
fi
echo "  MBR: sudo dd if=$BOOT_DEVICE bs=1 skip=512 count=27 | hexdump -C"
echo

echo "=============================================="
echo "Verification complete!"
echo "=============================================="
