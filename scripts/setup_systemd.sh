#!/bin/bash
# MovieCP Systemd Setup Script

set -e

echo "=== MovieCP Systemd Setup ==="
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)"
   exit 1
fi

# Copy service files
echo "Copying systemd service files..."
cp /opt/moviecp/systemd/moviecp-watcher.service /etc/systemd/system/
cp /opt/moviecp/systemd/moviecp-web.service /etc/systemd/system/

# Reload systemd daemon
echo "Reloading systemd daemon..."
systemctl daemon-reload

# Enable services
echo "Enabling services..."
systemctl enable moviecp-watcher.service
systemctl enable moviecp-web.service

# Start services
echo "Starting services..."
systemctl start moviecp-watcher.service
systemctl start moviecp-web.service

# Wait a moment for services to start
sleep 2

# Check status
echo ""
echo "=== Service Status ==="
echo ""
echo "File Watcher:"
systemctl status moviecp-watcher.service --no-pager
echo ""
echo "Web Dashboard:"
systemctl status moviecp-web.service --no-pager

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Services are now running!"
echo ""
echo "Useful commands:"
echo "  - View watcher logs: sudo journalctl -u moviecp-watcher -f"
echo "  - View web logs: sudo journalctl -u moviecp-web -f"
echo "  - Restart watcher: sudo systemctl restart moviecp-watcher"
echo "  - Restart web: sudo systemctl restart moviecp-web"
echo "  - Stop all: sudo systemctl stop moviecp-watcher moviecp-web"
echo ""
