#!/bin/bash
#
# late.sh - Post-installation script for Ubuntu autoinstall
# Version: 1.0.1
# Purpose: Runs during late-commands phase to perform final system configuration
#

set -e  # Exit on any error

# Function to pause with message
pause_with_message() {
    echo ""
    echo "⏸️  $1"
    echo "   Press Enter to continue, or Ctrl+C to exit..."
    read -r
}

# Function to auto-pause with timeout
auto_pause() {
    local seconds=${1:-5}
    echo ""
    echo "⏸️  Pausing for $seconds seconds... (Press any key to continue immediately)"
    read -t $seconds -n 1 || true
    echo ""
}

# Log all output
exec > >(tee -a /var/log/late-install.log) 2>&1

echo "============================================="
echo "Late Install Script - Starting at $(date)"
echo "============================================="

# Check if running during installation (chroot environment)
if [ -d "/target" ]; then
    echo "🔧 Running in autoinstall environment (chroot)"
    TARGET_ROOT="/target"
    CHROOT_CMD="chroot /target"
else
    echo "🖥️  Running in normal environment"
    TARGET_ROOT=""
    CHROOT_CMD=""
fi

auto_pause 3

# System information
echo "System Information:"
echo "  - Hostname: $(hostname)"
echo "  - OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
echo "  - Kernel: $(uname -r)"
echo "  - Architecture: $(uname -m)"
echo "  - Memory: $(free -h | grep Mem | awk '{print $2}')"
echo "  - Disk Space: $(df -h / | tail -1 | awk '{print $4}' | tr -d '\n') available"

pause_with_message "System information displayed"

# Verify minimal server installation
echo ""
echo "Verifying minimal server installation:"
if [ -n "$TARGET_ROOT" ]; then
    if $CHROOT_CMD dpkg -l | grep -q ubuntu-server-minimal; then
        echo "  ✅ ubuntu-server-minimal is installed"
    else
        echo "  ❌ ubuntu-server-minimal NOT found"
    fi
else
    if dpkg -l | grep -q ubuntu-server-minimal; then
        echo "  ✅ ubuntu-server-minimal is installed"
    else
        echo "  ❌ ubuntu-server-minimal NOT found"
    fi
fi

auto_pause 2

# Check SSH status
echo ""
echo "Verifying SSH configuration:"
if [ -n "$TARGET_ROOT" ]; then
    if $CHROOT_CMD systemctl is-enabled ssh >/dev/null 2>&1; then
        echo "  ❌ SSH is enabled (should be disabled)"
    else
        echo "  ✅ SSH is disabled"
    fi
else
    if systemctl is-enabled ssh >/dev/null 2>&1; then
        echo "  ❌ SSH is enabled (should be disabled)"
    else
        echo "  ✅ SSH is disabled"
    fi
fi

auto_pause 2

# Check snap status
echo ""
echo "Verifying snap configuration:"
if [ -n "$TARGET_ROOT" ]; then
    if $CHROOT_CMD systemctl is-enabled snapd >/dev/null 2>&1; then
        echo "  ❌ snapd is enabled (should be disabled)"
    else
        echo "  ✅ snapd is disabled"
    fi
else
    if systemctl is-enabled snapd >/dev/null 2>&1; then
        echo "  ❌ snapd is enabled (should be disabled)"
    else
        echo "  ✅ snapd is disabled"
    fi
fi

pause_with_message "Configuration verification complete"

# Show installed packages count
echo ""
echo "Package information:"
if [ -n "$TARGET_ROOT" ]; then
    TOTAL_PACKAGES=$($CHROOT_CMD dpkg -l | grep -c "^ii")
else
    TOTAL_PACKAGES=$(dpkg -l | grep -c "^ii")
fi
echo "  - Total packages installed: $TOTAL_PACKAGES"

auto_pause 2

# Show disk usage
echo ""
echo "Disk usage:"
df -h

auto_pause 3

# Network configuration verification
echo ""
echo "Network configuration:"
ip addr show | grep -E "^[0-9]+:|inet " | head -10

auto_pause 2

# System services status
echo ""
echo "Key system services:"
for service in systemd-resolved networking; do
    if [ -n "$TARGET_ROOT" ]; then
        if $CHROOT_CMD systemctl is-active $service >/dev/null 2>&1; then
            echo "  ✅ $service is running"
        else
            echo "  ❌ $service is not running"
        fi
    else
        if systemctl is-active $service >/dev/null 2>&1; then
            echo "  ✅ $service is running"
        else
            echo "  ❌ $service is not running"
        fi
    fi
done

pause_with_message "Service status check complete"

# Custom configuration could go here
echo ""
echo "Custom configuration section:"
echo "  - Add any custom system configuration here"
echo "  - Examples: firewall rules, custom users, additional packages"

auto_pause 2

# Final system cleanup
echo ""
echo "Performing final cleanup:"
if [ -n "$TARGET_ROOT" ]; then
    $CHROOT_CMD apt-get autoremove -y >/dev/null 2>&1 || true
    $CHROOT_CMD apt-get autoclean -y >/dev/null 2>&1 || true
else
    apt-get autoremove -y >/dev/null 2>&1 || true
    apt-get autoclean -y >/dev/null 2>&1 || true
fi
echo "  ✅ System cleanup completed"

echo ""
echo "============================================="
echo "Late Install Script - Completed at $(date)"
echo "============================================="
echo "Log saved to: /var/log/late-install.log"

# Final pause before exit
pause_with_message "Script completed. Review the output above."