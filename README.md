# MovieCP - Movie Copy Daemon

A Linux daemon that monitors download folders for new movie files, provides a web dashboard for approval/rejection, and automatically copies approved movies to a network share with intelligent renaming via mnamer.

## Features

- **Automatic File Monitoring**: Watches download folder for new movie files (≥500 MB)
- **Web Dashboard**: Accessible from any device on your network for approving/rejecting movies
- **Intelligent Renaming**: Uses mnamer to automatically rename movies with proper formatting
- **Version Detection**: Automatically appends .v2, .v3, etc. when duplicate movies are detected
- **Systemd Integration**: Runs as persistent system services
- **File Validation**: Filters out incomplete downloads and non-video files
- **Comprehensive Logging**: Detailed logs for debugging and monitoring

## Architecture

The application consists of two services:

1. **File Watcher Service**: Monitors download folder and adds new movies to the database
2. **Web Dashboard Service**: FastAPI-based web interface for managing pending movies

## Requirements

- Linux server (Ubuntu 20.04+ recommended)
- Python 3.10 or higher
- Network share mounted (SMB/CIFS or NFS)
- mnamer installed

## Installation

### 1. Clone the Repository

```bash
cd /opt
git clone <your-repo-url> moviecp
cd moviecp
```

### 2. Run Installation Script

```bash
bash scripts/install.sh
```

This script will:
- Install system dependencies
- Create moviecp user
- Set up Python virtual environment
- Install Python dependencies
- Create required directories
- Copy configuration template

### 3. Configure the Application

Edit the configuration file:

```bash
sudo nano /etc/moviecp/config.yaml
```

**Important settings to configure:**

```yaml
watcher:
  download_folder: "/home/youruser/downloads/movies"  # Your download folder
  min_file_size_mb: 500  # Minimum file size (500 MB default)

network_share:
  mount_path: "/mnt/movies"  # Where your network share is mounted
  target_folder: "Movies"  # Subfolder within mount_path

web:
  host: "0.0.0.0"  # Bind to all interfaces
  port: 8080  # Web dashboard port

database:
  path: "/var/lib/moviecp/moviecp.db"

logging:
  level: "INFO"
  file: "/var/log/moviecp/moviecp.log"
```

### 4. Mount Network Share (if not already mounted)

Create mount point:
```bash
sudo mkdir -p /mnt/movies
```

Mount via CIFS/SMB:
```bash
sudo mount -t cifs //server/movies /mnt/movies -o username=youruser,password=yourpass
```

Or add to `/etc/fstab` for automatic mounting:
```
//server/movies /mnt/movies cifs credentials=/home/user/.smbcredentials,uid=moviecp,gid=moviecp 0 0
```

### 5. Initialize Database

```bash
cd /opt/moviecp
sudo -u moviecp venv/bin/python -m moviecp init-db
```

### 6. Setup Systemd Services

```bash
sudo bash scripts/setup_systemd.sh
```

This will:
- Copy service files to /etc/systemd/system/
- Enable services to start on boot
- Start both services

### 7. Access Web Dashboard

Open your browser and navigate to:
```
http://<server-ip>:8080
```

You should see the MovieCP dashboard!

## Usage

### Web Dashboard

The web dashboard allows you to:
- View all pending movies detected in the download folder
- Approve movies (copies to network share with renaming)
- Reject movies (removes from queue)
- View statistics (pending, approved, rejected counts)

**Approving a Movie:**
1. Movie appears in the dashboard after being detected
2. Click "Approve" button
3. The system will:
   - Run mnamer to generate proper filename
   - Check for existing versions (.v2, .v3, etc.)
   - Copy file to network share
   - Update database

**Rejecting a Movie:**
1. Click "Reject" button
2. Confirm the rejection
3. Movie is removed from pending queue (source file optionally deleted)

### Command Line

**View logs:**
```bash
# File watcher logs
sudo journalctl -u moviecp-watcher -f

# Web dashboard logs
sudo journalctl -u moviecp-web -f
```

**Manage services:**
```bash
# Restart services
sudo systemctl restart moviecp-watcher
sudo systemctl restart moviecp-web

# Stop services
sudo systemctl stop moviecp-watcher moviecp-web

# Check status
sudo systemctl status moviecp-watcher
sudo systemctl status moviecp-web
```

**Run manually (for testing):**
```bash
cd /opt/moviecp
sudo -u moviecp venv/bin/python -m moviecp watcher  # File watcher
sudo -u moviecp venv/bin/python -m moviecp web      # Web dashboard
```

## Configuration Reference

### Watcher Settings

- `download_folder`: Directory to monitor for new movies
- `min_file_size_mb`: Minimum file size in MB (default: 500)
- `stable_time_seconds`: Wait time to ensure download is complete (default: 30)
- `supported_extensions`: List of video file extensions to monitor

### Network Share Settings

- `mount_path`: Path where network share is mounted
- `target_folder`: Subfolder within mount_path to store movies
- `verify_mount`: Check if share is accessible before operations

### Version Detection

- `enabled`: Enable/disable version detection (default: true)
- `format`: Version suffix format (default: ".v{number}")
- `similarity_threshold`: Similarity threshold for fuzzy matching (default: 0.9)

### Web Dashboard

- `host`: Host to bind web server (default: "0.0.0.0")
- `port`: Port for web dashboard (default: 8080)

## Troubleshooting

### Movies not appearing in dashboard

1. Check if file watcher service is running:
   ```bash
   sudo systemctl status moviecp-watcher
   ```

2. Check logs:
   ```bash
   sudo journalctl -u moviecp-watcher -n 50
   ```

3. Verify download folder path in config
4. Ensure files are ≥500 MB and have supported extensions

### File copy failures

1. Check network share is mounted:
   ```bash
   ls /mnt/movies
   ```

2. Check permissions:
   ```bash
   sudo -u moviecp touch /mnt/movies/test.txt
   ```

3. Check logs for specific error messages

### mnamer not working

1. Verify mnamer is installed:
   ```bash
   mnamer --version
   ```

2. Test mnamer manually:
   ```bash
   mnamer /path/to/movie.mkv --batch
   ```

### Web dashboard not accessible

1. Check if web service is running:
   ```bash
   sudo systemctl status moviecp-web
   ```

2. Verify port is not blocked by firewall:
   ```bash
   sudo ufw allow 8080
   ```

3. Check if port is in use:
   ```bash
   sudo netstat -tulpn | grep 8080
   ```

## File Locations

- Application: `/opt/moviecp`
- Configuration: `/etc/moviecp/config.yaml`
- Database: `/var/lib/moviecp/moviecp.db`
- Logs: `/var/log/moviecp/moviecp.log`
- Service files: `/etc/systemd/system/moviecp-*.service`

## API Endpoints

The web dashboard exposes a REST API:

- `GET /api/movies/pending` - List pending movies
- `GET /api/movies/history?limit=50` - List processed movies
- `POST /api/movies/{id}/approve` - Approve a movie
- `POST /api/movies/{id}/reject` - Reject a movie
- `GET /api/stats` - Get statistics
- `GET /api/health` - Health check

## Development

### Running Tests

```bash
cd /opt/moviecp
source venv/bin/activate
pytest tests/
```

### Manual Testing

1. Copy a test movie file (>500 MB) to download folder
2. Watch logs: `sudo journalctl -u moviecp-watcher -f`
3. Check web dashboard for new movie
4. Test approve/reject functionality

## Uninstallation

To cleanly remove MovieCP from your Debian server:

```bash
sudo bash /opt/moviecp/scripts/uninstall.sh
```

The uninstall script will:
- Stop and disable both systemd services
- Remove service files and reload systemd
- Remove application directory (`/opt/moviecp`)
- Ask if you want to remove data files (database, logs, config)
- Ask if you want to remove the `moviecp` system user

**Interactive prompts:**
- Confirm uninstall
- Choose to keep or remove data files
- Choose to keep or remove system user

If you choose to keep data files, you can manually remove them later:
```bash
sudo rm -rf /var/lib/moviecp  # Database
sudo rm -rf /var/log/moviecp  # Logs
sudo rm -rf /etc/moviecp      # Configuration
```

## Security Considerations

- The daemon runs as non-root `moviecp` user
- Consider adding authentication to web dashboard for production
- Restrict web dashboard port via firewall if exposed to internet
- Store SMB credentials securely (not in config.yaml)

## Contributing

Contributions are welcome! Please submit pull requests or open issues for bugs and feature requests.

## License

MIT License - see LICENSE file for details

## Support

For issues and questions, please open a GitHub issue.
