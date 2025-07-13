#!/usr/bin/env python3
"""
Test script for autoinstall functionality
Verifies that the autoinstall configuration files are correctly created and integrated
"""

import os
import sys
import yaml
import subprocess

def test_autoinstall_files():
    """Test that autoinstall configuration files exist and are valid"""
    print("Testing autoinstall configuration files...")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Test user-data file
    user_data_path = os.path.join(script_dir, "autoinstall-user-data")
    if not os.path.exists(user_data_path):
        print(f"✗ FAIL: {user_data_path} not found")
        return False
    
    try:
        with open(user_data_path, 'r') as f:
            user_data = yaml.safe_load(f)
        
        # Check required sections
        if 'autoinstall' not in user_data:
            print("✗ FAIL: autoinstall section missing from user-data")
            return False
        
        autoinstall = user_data['autoinstall']
        
        # Check version
        if autoinstall.get('version') != 1:
            print("✗ FAIL: autoinstall version should be 1")
            return False
        
        # Check interactive sections
        interactive_sections = autoinstall.get('interactive-sections', [])
        expected_interactive = ['locale', 'keyboard', 'network', 'proxy', 'storage', 'identity', 'ubuntu-pro', 'drivers']
        
        for section in expected_interactive:
            if section not in interactive_sections:
                print(f"✗ FAIL: {section} not in interactive-sections")
                return False
        
        # Check forced configurations
        ssh_config = autoinstall.get('ssh', {})
        if ssh_config.get('install-server') != False:
            print("✗ FAIL: SSH server should be disabled")
            return False
        
        packages = autoinstall.get('packages', [])
        if 'ubuntu-server-minimal' not in packages:
            print("✗ FAIL: ubuntu-server-minimal not in packages")
            return False
        
        snaps = autoinstall.get('snaps', [])
        if len(snaps) != 0:
            print("✗ FAIL: snaps should be empty")
            return False
        
        drivers = autoinstall.get('drivers', {})
        if drivers.get('install') != True:
            print("✗ FAIL: drivers install should be True")
            return False
        
        print("✓ PASS: user-data configuration is valid")
        
    except yaml.YAMLError as e:
        print(f"✗ FAIL: user-data YAML parsing error: {e}")
        return False
    
    # Test meta-data file
    meta_data_path = os.path.join(script_dir, "autoinstall-meta-data")
    if not os.path.exists(meta_data_path):
        print(f"✗ FAIL: {meta_data_path} not found")
        return False
    
    try:
        with open(meta_data_path, 'r') as f:
            meta_data = yaml.safe_load(f)
        
        if 'instance-id' not in meta_data:
            print("✗ FAIL: instance-id missing from meta-data")
            return False
        
        print("✓ PASS: meta-data configuration is valid")
        
    except yaml.YAMLError as e:
        print(f"✗ FAIL: meta-data YAML parsing error: {e}")
        return False
    
    # Test GRUB configuration
    grub_config_path = os.path.join(script_dir, "grub-autoinstall.cfg")
    if not os.path.exists(grub_config_path):
        print(f"✗ FAIL: {grub_config_path} not found")
        return False
    
    with open(grub_config_path, 'r') as f:
        grub_content = f.read()
    
    if "autoinstall ds=nocloud-net;s=/cdrom/server/" not in grub_content:
        print("✗ FAIL: GRUB configuration missing autoinstall boot option")
        return False
    
    if "Install Ubuntu Server (Semi-Automated)" not in grub_content:
        print("✗ FAIL: GRUB configuration missing semi-automated menu entry")
        return False
    
    print("✓ PASS: GRUB configuration is valid")
    
    return True

def test_remaster_script():
    """Test that the remaster script has autoinstall functionality"""
    print("\nTesting remaster script integration...")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    remaster_path = os.path.join(script_dir, "remaster.py")
    
    if not os.path.exists(remaster_path):
        print(f"✗ FAIL: {remaster_path} not found")
        return False
    
    with open(remaster_path, 'r') as f:
        remaster_content = f.read()
    
    # Check for autoinstall function
    if "def inject_autoinstall_files" not in remaster_content:
        print("✗ FAIL: inject_autoinstall_files function not found")
        return False
    
    # Check for autoinstall argument parsing
    if "inject_autoinstall = \"-autoinstall\" in sys.argv" not in remaster_content:
        print("✗ FAIL: autoinstall argument parsing not found")
        return False
    
    # Check for autoinstall function call
    if "inject_autoinstall_files(work_dir)" not in remaster_content:
        print("✗ FAIL: autoinstall function call not found")
        return False
    
    # Check version update
    if "Version: 0.02.7" not in remaster_content:
        print("✗ FAIL: version not updated to 0.02.7")
        return False
    
    print("✓ PASS: remaster script has autoinstall integration")
    
    return True

def demonstrate_usage():
    """Demonstrate how to use the autoinstall functionality"""
    print("\n" + "="*50)
    print("AUTOINSTALL FUNCTIONALITY DEMONSTRATION")
    print("="*50)
    
    print("\nTo create an autoinstall ISO, run:")
    print("  python3 remaster.py -autoinstall")
    
    print("\nThis will create an ISO with the following behavior:")
    print("\n📋 INTERACTIVE CHOICES (User selects):")
    print("  ✓ Language")
    print("  ✓ Keyboard layout")
    print("  ✓ Network configuration")
    print("  ✓ Proxy configuration")
    print("  ✓ Storage configuration")
    print("  ✓ Profile setup (name, username, password)")
    print("  ✓ Ubuntu Pro upgrade")
    print("  ✓ Third-party drivers")
    
    print("\n🔒 FORCED CHOICES (Pre-configured):")
    print("  ✓ Ubuntu Server (minimized) installation")
    print("  ✓ Search for third-party drivers enabled")
    print("  ✓ SSH server disabled")
    print("  ✓ No featured server snaps")
    
    print("\n🚀 BOOT MENU OPTIONS:")
    print("  1. Install Ubuntu Server (Semi-Automated) ← Uses autoinstall")
    print("  2. Install Ubuntu Server (Manual) ← Standard installation")
    print("  3. Try Ubuntu Server without installing")
    
    print("\n📁 Files created:")
    print("  /server/user-data    ← Main autoinstall configuration")
    print("  /server/meta-data    ← Cloud-init metadata")
    print("  /boot/grub/grub.cfg  ← Modified GRUB menu")

def main():
    """Main test function"""
    print("Ubuntu 24.04.2 Autoinstall Configuration Test")
    print("="*50)
    
    success = True
    
    # Test configuration files
    if not test_autoinstall_files():
        success = False
    
    # Test remaster script integration
    if not test_remaster_script():
        success = False
    
    # Show usage demonstration
    demonstrate_usage()
    
    print("\n" + "="*50)
    if success:
        print("✓ ALL TESTS PASSED - Autoinstall functionality is ready!")
        print("\nTo create your autoinstall ISO, run:")
        print("  python3 remaster.py -autoinstall")
        return 0
    else:
        print("✗ SOME TESTS FAILED - Check the errors above")
        return 1

if __name__ == "__main__":
    sys.exit(main())