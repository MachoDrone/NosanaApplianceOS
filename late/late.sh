#!/bin/bash
#
# late.sh - Post-installation script for Ubuntu autoinstall
# Version: 1.0.0
# Purpose: Runs during late-commands phase to perform final system configuration
#

set -e  # Exit on any error

# Log all output
exec > >(tee -a /var/log/late-install.log) 2>&1

echo "============================================="
echo "Late Install Script - Starting at $(date)"
echo "============================================="

# System information
echo "System Information:"
echo "  - Hostname: $(hostname)"
echo "  - OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
echo "  - Kernel: $(uname -r)"
echo "  - Architecture: $(uname -m)"
echo "  - Memory: $(free -h | grep Mem | awk '{print $2}')"
echo "  - Disk Space: $(df -h / | tail -1 | awk '{print $4}' | tr -d '\n') available"

# Verify minimal server installation
echo ""
echo "Verifying minimal server installation:"
if dpkg -l | grep -q ubuntu-server-minimal; then
    echo "  ✅ ubuntu-server-minimal is installed"
else
    echo "  ❌ ubuntu-server-minimal NOT found"
fi

# Check SSH status
echo ""
echo "Verifying SSH configuration:"
if systemctl is-enabled ssh >/dev/null 2>&1; then
    echo "  ❌ SSH is enabled (should be disabled)"
else
    echo "  ✅ SSH is disabled"
fi

# Check snap status
echo ""
echo "Verifying snap configuration:"
if systemctl is-enabled snapd >/dev/null 2>&1; then
    echo "  ❌ snapd is enabled (should be disabled)"
else
    echo "  ✅ snapd is disabled"
fi

# Show installed packages count
echo ""
echo "Package information:"
TOTAL_PACKAGES=$(dpkg -l | grep -c "^ii")
echo "  - Total packages installed: $TOTAL_PACKAGES"

# Show disk usage
echo ""
echo "Disk usage:"
df -h

# Network configuration verification
echo ""
echo "Network configuration:"
ip addr show | grep -E "^[0-9]+:|inet " | head -10

# System services status
echo ""
echo "Key system services:"
for service in systemd-resolved networking; do
    if systemctl is-active $service >/dev/null 2>&1; then
        echo "  ✅ $service is running"
    else
        echo "  ❌ $service is not running"
    fi
done

# Custom configuration could go here
echo ""
echo "Custom configuration section:"
echo "  - Add any custom system configuration here"
echo "  - Examples: firewall rules, custom users, additional packages"

# Final system cleanup
echo ""
echo "Performing final cleanup:"
apt-get autoremove -y >/dev/null 2>&1 || true
apt-get autoclean -y >/dev/null 2>&1 || true
echo "  ✅ System cleanup completed"

echo ""
echo "============================================="
echo "Late Install Script - Completed at $(date)"
echo "============================================="
echo "Log saved to: /var/log/late-install.log"