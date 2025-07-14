# Quick Start Guide for Ubuntu 24.04.2 Autoinstall

## Option 1: Run Standalone Version (Recommended for remote usage)

The standalone version includes all autoinstall configuration files inline, so you can run it directly from GitHub:

```bash
wget -O - https://raw.githubusercontent.com/MachoDrone/NosanaApplianceOS/refs/heads/cursor/create-customizable-auto-installer-options-e879/remaster/remaster-standalone.py | python3 - -autoinstall
```

## Option 2: Use Local Modular Version

If you prefer to work with separate configuration files:

```bash
git clone https://github.com/MachoDrone/NosanaApplianceOS.git
cd NosanaApplianceOS/remaster
python3 remaster.py -autoinstall
```

## What You'll Get

Both methods create an ISO called `NosanaAOS-0.24.04.2.iso` with:

### 📋 Interactive Choices (Users can select):
- Language
- Keyboard layout  
- Network configuration
- Proxy configuration
- Storage configuration
- Profile setup (name, username, password)
- Ubuntu Pro upgrade
- Third-party drivers

### 🔒 Forced Choices (Pre-configured):
- Ubuntu Server (minimized) installation
- Search for third-party drivers enabled
- SSH server disabled
- No featured server snaps

### 🚀 Boot Menu Options:
1. **Install Ubuntu Server (Semi-Automated)** ← Uses autoinstall
2. **Install Ubuntu Server (Manual)** ← Standard installation
3. **Try Ubuntu Server without installing** ← Live environment

## Command Line Options

- `-autoinstall` - Enable autoinstall functionality
- `-hello` - Include HelloNOS test files
- `-dc` - Disable cleanup (keep temp files)

Examples:
```bash
# Basic autoinstall
python3 remaster.py -autoinstall

# With test files and debug
python3 remaster.py -autoinstall -hello -dc

# Remote standalone version
wget -O - https://raw.githubusercontent.com/.../remaster-standalone.py | python3 - -autoinstall -dc
```

## Testing Your ISO

After creating the ISO, test it in a virtual machine:
1. Boot from the ISO
2. Select "Install Ubuntu Server (Semi-Automated)"
3. Verify that forced choices are applied
4. Complete the interactive sections

## File Structure

**Standalone version**: Everything is included in one file
**Modular version**: Separate configuration files for customization
- `autoinstall-user-data` - Main autoinstall configuration
- `autoinstall-meta-data` - Cloud-init metadata
- `grub-autoinstall.cfg` - GRUB menu configuration

## Next Steps

1. Test the ISO in a VM first
2. Customize the configuration for your specific needs
3. Deploy to your customers
4. Provide clear boot instructions to select the semi-automated option