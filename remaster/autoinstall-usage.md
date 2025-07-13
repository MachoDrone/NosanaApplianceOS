# Ubuntu 24.04.2 Autoinstall Usage Guide

## Overview
The autoinstall functionality creates a semi-automated Ubuntu Server installer that allows users to make interactive choices for specific components while forcing certain configurations.

## How to Use

### 1. Create the Autoinstall ISO
```bash
cd remaster
python3 remaster.py -autoinstall
```

This will:
- Download Ubuntu 24.04.2 Server ISO
- Extract and modify the ISO contents
- Inject autoinstall configuration files
- Create a new ISO: `NosanaAOS-0.24.04.2.iso`

### 2. Boot from the Modified ISO
When you boot from the remastered ISO, you'll see a GRUB menu with these options:
- **Install Ubuntu Server (Semi-Automated)** - Uses autoinstall with interactive sections
- **Install Ubuntu Server (Manual)** - Standard manual installation
- **Try Ubuntu Server without installing** - Live environment

### 3. Interactive vs Forced Choices

#### Interactive Choices (User can select):
- **Language** - Choose from available languages
- **Keyboard** - Select keyboard layout
- **Network configuration** - Configure network settings
- **Proxy Configuration** - Set proxy settings and test mirror locations
- **Guided storage configuration** - Choose storage layout options
- **Storage configuration** - Configure disk partitioning
- **Profile configuration** - Enter your name, username, server name, password
- **Upgrade to Ubuntu Pro** - Default is "Skip for now" but user can choose
- **Third-party drivers** - User can select which drivers to install

#### Forced Choices (Pre-configured):
- **Type of installation**: Ubuntu Server (minimized) - automatically selected
- **Search for third-party drivers**: Enabled by default
- **SSH configuration**: OpenSSH Server will NOT be installed (unchecked)
- **Featured server snaps**: No snaps will be pre-selected

## Configuration Files

### autoinstall-user-data
This is the main configuration file that defines:
- Which sections are interactive
- Forced package selections (ubuntu-server-minimal)
- SSH configuration (disabled)
- Snap configuration (none selected)
- Driver installation (enabled)

### autoinstall-meta-data
Contains basic instance metadata for cloud-init.

### grub-autoinstall.cfg
Modified GRUB configuration that adds the autoinstall boot option.

## Customization

### Modifying Interactive Sections
Edit `autoinstall-user-data` and modify the `interactive-sections` list:
```yaml
interactive-sections:
  - locale
  - keyboard
  - network
  - proxy
  - storage
  - identity
  - ubuntu-pro
  - drivers
```

### Forcing Additional Choices
To force specific configurations, modify the corresponding sections in `autoinstall-user-data`. For example, to force a specific network configuration:
```yaml
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: true
```

### Adding Pre-installed Packages
Modify the `packages` section:
```yaml
packages:
  - ubuntu-server-minimal
  - htop
  - vim
  - curl
```

## Command Line Options

### Available Arguments:
- `python3 remaster.py` - Standard remastering without autoinstall
- `python3 remaster.py -autoinstall` - Include autoinstall configuration
- `python3 remaster.py -hello` - Include HelloNOS test files
- `python3 remaster.py -dc` - Disable cleanup (keep temp files)
- `python3 remaster.py -autoinstall -hello -dc` - Combine multiple options

## File Structure
After running with `-autoinstall`, the ISO will contain:
```
/server/
  ├── user-data          # Main autoinstall configuration
  └── meta-data          # Cloud-init metadata
/boot/grub/
  └── grub.cfg           # Modified with autoinstall menu option
```

## Troubleshooting

### Common Issues:
1. **Autoinstall not triggered**: Ensure you select "Install Ubuntu Server (Semi-Automated)" from the GRUB menu
2. **Configuration not applied**: Check that the `/server/user-data` file exists on the ISO
3. **SSH still enabled**: Verify the `ssh.install-server: false` setting in user-data

### Debug Mode:
Use the `-dc` flag to keep temp files for debugging:
```bash
python3 remaster.py -autoinstall -dc
```

This will preserve the extracted ISO contents in the `working_dir/` folder for inspection.

## Benefits
- **Consistent installations** - Forces specific configurations across deployments
- **Reduced user errors** - Eliminates possibility of selecting unwanted options
- **Faster deployment** - Reduces the number of manual selections required
- **Flexible customization** - Easy to modify which options are interactive vs forced