#!/bin/bash
# MovieCP Uninstall Script

set -e

echo "=== MovieCP Uninstall Script ==="
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)"
   exit 1
fi

# Confirm uninstall
echo "WARNING: This will remove MovieCP from your system."
echo ""
read -p "Are you sure you want to continue? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Uninstall cancelled."
    exit 0
fi

# Ask about data removal
echo ""
echo "Do you want to remove data files? (database, logs, configuration)"
read -p "Remove data? (yes/no): " remove_data

echo ""
echo "Starting uninstall process..."
echo ""

# Stop services if running
echo "Stopping services..."
systemctl stop moviecp-watcher.service 2>/dev/null || echo "  moviecp-watcher service not running"
systemctl stop moviecp-web.service 2>/dev/null || echo "  moviecp-web service not running"

# Disable services
echo "Disabling services..."
systemctl disable moviecp-watcher.service 2>/dev/null || echo "  moviecp-watcher service not enabled"
systemctl disable moviecp-web.service 2>/dev/null || echo "  moviecp-web service not enabled"

# Remove systemd service files
echo "Removing systemd service files..."
rm -f /etc/systemd/system/moviecp-watcher.service
rm -f /etc/systemd/system/moviecp-web.service

# Reload systemd daemon
echo "Reloading systemd daemon..."
systemctl daemon-reload
systemctl reset-failed

# Remove application directory
if [ -d "/opt/moviecp" ]; then
    echo "Removing application files from /opt/moviecp..."
    rm -rf /opt/moviecp
else
    echo "Application directory /opt/moviecp not found (already removed?)"
fi

# Remove data if requested
if [ "$remove_data" = "yes" ]; then
    echo "Removing data files..."

    # Remove database and backup directories
    if [ -d "/var/lib/moviecp" ]; then
        echo "  Removing database directory: /var/lib/moviecp"
        rm -rf /var/lib/moviecp
    fi

    # Remove logs
    if [ -d "/var/log/moviecp" ]; then
        echo "  Removing log directory: /var/log/moviecp"
        rm -rf /var/log/moviecp
    fi

    # Remove configuration
    if [ -d "/etc/moviecp" ]; then
        echo "  Removing configuration directory: /etc/moviecp"
        rm -rf /etc/moviecp
    fi
else
    echo "Keeping data files (database, logs, configuration)"
    echo "  Database: /var/lib/moviecp/"
    echo "  Logs: /var/log/moviecp/"
    echo "  Configuration: /etc/moviecp/"
fi

# Ask about removing user
echo ""
read -p "Remove moviecp system user? (yes/no): " remove_user
if [ "$remove_user" = "yes" ]; then
    if id "moviecp" &>/dev/null; then
        echo "Removing moviecp user..."
        userdel moviecp 2>/dev/null || echo "  Warning: Could not remove user (may have running processes)"
    else
        echo "User moviecp does not exist (already removed?)"
    fi
else
    echo "Keeping moviecp user"
fi

echo ""
echo "=== Uninstall Complete ==="
echo ""

if [ "$remove_data" != "yes" ]; then
    echo "Data files were preserved. To remove them manually:"
    echo "  sudo rm -rf /var/lib/moviecp"
    echo "  sudo rm -rf /var/log/moviecp"
    echo "  sudo rm -rf /etc/moviecp"
    echo ""
fi

if [ "$remove_user" != "yes" ]; then
    echo "The moviecp user was preserved. To remove manually:"
    echo "  sudo userdel moviecp"
    echo ""
fi

echo "MovieCP has been uninstalled from your system."
echo ""
