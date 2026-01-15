# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MovieCP is a Linux daemon system that automates movie file management. It monitors a download folder, presents new movies via a web dashboard for approval, and copies approved movies to a network share with intelligent renaming via mnamer and version detection.

## Architecture

The system consists of **two independent services** that share a SQLite database:

1. **File Watcher Service** (`moviecp watcher`)
   - Monitors download folder using Watchdog
   - Validates files (size ≥500 MB, video extensions, stability)
   - Inserts pending movies into database
   - Runs continuously as a systemd service

2. **Web Dashboard Service** (`moviecp web`)
   - FastAPI web server with REST API
   - Serves Jinja2 templates with HTMX for dynamic updates
   - Orchestrates approval workflow via MovieManager
   - Runs continuously as a systemd service

### Key Architectural Patterns

**Configuration**: Single source of truth via Pydantic models in `moviecp/config.py`. Config is loaded from YAML and validated on startup. The config path search order is: `config/config.yaml`, `/etc/moviecp/config.yaml`, `~/.config/moviecp/config.yaml`.

**Database**: SQLite with WAL mode for concurrent access. Two main tables:
- `pending_movies`: Movies awaiting approval (managed by watcher)
- `processed_movies`: Historical record of approved/rejected movies

**Approval Workflow** (orchestrated by `MovieManager`):
1. Run mnamer subprocess to get renamed filename
2. Check network share for existing versions using fuzzy matching
3. Stream-copy file in chunks (memory-efficient)
4. Verify copy with size check
5. Move record from `pending_movies` to `processed_movies`

**Error Handling**: All core operations have retry logic with exponential backoff. Errors update movie status to 'failed' with error_message stored in database.

## Development Commands

### Running Locally

```bash
# Activate virtual environment
source venv/bin/activate  # or: venv/bin/activate on Linux

# Initialize database
python -m moviecp init-db

# Run file watcher (blocking)
python -m moviecp watcher

# Run web dashboard (blocking)
python -m moviecp web

# Run with custom config
python -m moviecp watcher -c /path/to/config.yaml
```

### Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=moviecp tests/

# Manual integration test:
# 1. Copy test file >500MB to download folder
# 2. Watch logs and verify it appears in dashboard
# 3. Approve via dashboard and verify copy to network share
```

### Service Management (Production)

```bash
# View logs
sudo journalctl -u moviecp-watcher -f
sudo journalctl -u moviecp-web -f

# Restart services
sudo systemctl restart moviecp-watcher moviecp-web

# Check status
sudo systemctl status moviecp-watcher
sudo systemctl status moviecp-web
```

## Critical Implementation Details

### File Stability Detection

The validator waits `stable_time_seconds` (default 30s) and checks if file size hasn't changed to avoid processing incomplete downloads. This is critical because the watcher triggers on file creation/modification events.

### Version Detection Algorithm

`VersionDetector` uses fuzzy string matching (SequenceMatcher) to detect duplicate movies even with slightly different names. It:
1. Strips extensions and existing version suffixes
2. Compares similarity (default threshold: 0.9)
3. Finds highest version number in matches
4. Returns next version (e.g., "Movie.v2.mkv")

### Streaming File Copy

`FileCopier` copies in 1MB chunks to handle large files without memory issues:
1. Writes to `.tmp` file during copy
2. Verifies size matches source
3. Renames to final path atomically
4. Retries up to 3 times with exponential backoff

### mnamer Integration

The `MovieRenamer` class wraps mnamer subprocess calls. It parses stdout for the arrow pattern (`"original" -> "renamed"`) to extract the new filename. If mnamer fails, the error is logged but the movie remains in pending state for manual intervention.

## Configuration Structure

Configuration is defined via Pydantic models with validation:

- `WatcherConfig`: download_folder (validated exists), min_file_size_mb, stable_time_seconds, supported_extensions, exclude_patterns
- `NetworkShareConfig`: mount_path (validated exists), target_folder, verify_mount
- `MnamerConfig`: executable_path, batch_mode, movie_format
- `VersionDetectionConfig`: enabled, format, similarity_threshold
- `DatabaseConfig`: path, backup settings
- `WebConfig`: host, port, cors_origins
- `LoggingConfig`: level, file, rotation settings

## Database Schema Notes

**pending_movies table**:
- `status` field: pending → processing → completed/failed
- Uses CHECK constraint to enforce valid status values
- `original_path` has UNIQUE constraint to prevent duplicates

**processed_movies table**:
- Records both approved and rejected movies
- `action` field: 'approved' or 'rejected' (CHECK constraint)
- `version_number`: 1 for original, 2+ for duplicates
- `mnamer_output`: Full stdout/stderr for debugging

## Web Dashboard Implementation

The dashboard uses **HTMX** for dynamic updates without full page reloads:
- Movie grid loads via `hx-get="/api/movies/pending"` on page load
- Custom JavaScript in `dashboard.html` transforms JSON to HTML cards
- Auto-refresh every 30 seconds
- Approve/reject buttons call REST API and remove card on success

**API Global State**: The `MovieManager` instance is created on FastAPI app startup and stored globally via `set_movie_manager()`. This ensures both watcher and web services use the same configuration.

## Common Issues

**mnamer not found**: Ensure mnamer is in PATH or set `executable_path` to full path in config.

**Permission errors on network share**: The daemon runs as user `moviecp`. Verify this user can write to mount_path: `sudo -u moviecp touch /mnt/movies/test.txt`

**Movies not appearing**: Check watcher logs for validation failures. Common causes: file <500MB, unsupported extension, or file path matching exclude_patterns.

**Database locked errors**: SQLite with WAL mode should handle concurrent access, but if both services try to write simultaneously during heavy load, one may retry. Check for `database.py` connection pooling settings.

## File Locations (Production)

- Application code: `/opt/moviecp/`
- Configuration: `/etc/moviecp/config.yaml`
- Database: `/var/lib/moviecp/moviecp.db`
- Logs: `/var/log/moviecp/moviecp.log`
- Virtual environment: `/opt/moviecp/venv/`
- Systemd services: `/etc/systemd/system/moviecp-{watcher,web}.service`
