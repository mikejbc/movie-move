#!/bin/bash
# MovieCP Installation Script

set -e

echo "=== MovieCP Installation Script ==="
echo ""

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "This script should NOT be run as root. Please run as a regular user with sudo privileges."
   exit 1
fi

# Install system dependencies
echo "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv

# Install mnamer
echo "Installing mnamer..."
pip3 install --user mnamer

# Create moviecp user if doesn't exist
if ! id "moviecp" &>/dev/null; then
    echo "Creating moviecp user..."
    sudo useradd -r -s /bin/false moviecp
else
    echo "User 'moviecp' already exists"
fi

# Create required directories
echo "Creating directories..."
sudo mkdir -p /opt/moviecp
sudo mkdir -p /var/lib/moviecp
sudo mkdir -p /var/log/moviecp
sudo mkdir -p /etc/moviecp

# Copy files to /opt/moviecp
echo "Copying application files..."
sudo cp -r . /opt/moviecp/

# Create Python virtual environment
echo "Creating Python virtual environment..."
cd /opt/moviecp
sudo python3 -m venv venv

# Install Python dependencies
echo "Installing Python dependencies..."
sudo /opt/moviecp/venv/bin/pip install --upgrade pip
sudo /opt/moviecp/venv/bin/pip install -r requirements.txt

# Copy config example
if [ ! -f /etc/moviecp/config.yaml ]; then
    echo "Copying configuration template..."
    sudo cp config/config.yaml.example /etc/moviecp/config.yaml
    echo "Please edit /etc/moviecp/config.yaml with your settings"
else
    echo "Configuration file already exists at /etc/moviecp/config.yaml"
fi

# Create symlink for config in local directory
if [ ! -f /opt/moviecp/config/config.yaml ]; then
    sudo ln -s /etc/moviecp/config.yaml /opt/moviecp/config/config.yaml
fi

# Set ownership
echo "Setting file permissions..."
sudo chown -R moviecp:moviecp /var/lib/moviecp
sudo chown -R moviecp:moviecp /var/log/moviecp
sudo chown -R moviecp:moviecp /opt/moviecp/venv

# Make scripts executable
sudo chmod +x /opt/moviecp/scripts/*.sh

echo ""
echo "=== Installation Complete ==="
echo ""
echo "Next steps:"
echo "1. Edit configuration: sudo nano /etc/moviecp/config.yaml"
echo "2. Initialize database: cd /opt/moviecp && sudo -u moviecp venv/bin/python -m moviecp init-db"
echo "3. Setup systemd services: sudo bash /opt/moviecp/scripts/setup_systemd.sh"
echo ""
