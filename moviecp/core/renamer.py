"""mnamer wrapper for renaming movie files."""
import os
import subprocess
from pathlib import Path
from typing import Optional, Tuple

from loguru import logger

from moviecp.config import MnamerConfig
from moviecp.utils.exceptions import MnamerError


class MovieRenamer:
    """Wrapper for mnamer tool."""

    def __init__(self, config: MnamerConfig):
        """
        Initialize movie renamer.

        Args:
            config: mnamer configuration.
        """
        self.config = config

    def rename_movie(self, file_path: str) -> Tuple[Optional[str], str]:
        """
        Use mnamer to generate new filename for a movie.

        Args:
            file_path: Path to the movie file.

        Returns:
            Tuple of (new_filename, mnamer_output).
            new_filename will be None if mnamer fails.

        Raises:
            MnamerError: If mnamer execution fails critically.
        """
        try:
            # Validate file path exists and is a file
            if not os.path.exists(file_path):
                raise MnamerError(f"File does not exist: {file_path}")
            
            if not os.path.isfile(file_path):
                raise MnamerError(f"Path is not a file: {file_path}")
            
            # Build mnamer command
            cmd = [self.config.executable_path]

            # Add batch mode flag
            if self.config.batch_mode:
                cmd.append("--batch")

            # Add media type
            cmd.extend(["--media", self.config.media_type])

            # Add movie format
            if self.config.movie_format:
                cmd.extend(["--movie-format", self.config.movie_format])

            # Add extra args
            cmd.extend(self.config.extra_args)

            # Add the file path (already validated)
            cmd.append(file_path)

            logger.info(f"Running mnamer: {' '.join(cmd)}")

            # Run mnamer with shell=False to prevent command injection
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,  # 1 minute timeout
                shell=False,  # Explicitly set to False for security
            )

            output = result.stdout + result.stderr

            logger.debug(f"mnamer exit code: {result.returncode}")
            logger.debug(f"mnamer output: {output}")

            # Check if mnamer was successful
            if result.returncode == 0:
                # Parse output to get new filename
                new_filename = self._parse_mnamer_output(output, file_path)

                if new_filename:
                    logger.success(f"mnamer renamed file to: {new_filename}")
                    return new_filename, output
                else:
                    logger.warning("Could not parse mnamer output for new filename")
                    return None, output
            else:
                logger.warning(f"mnamer failed with exit code {result.returncode}")
                return None, output

        except subprocess.TimeoutExpired:
            error_msg = f"mnamer timed out for file: {file_path}"
            logger.error(error_msg)
            raise MnamerError(error_msg)

        except FileNotFoundError:
            error_msg = f"mnamer executable not found: {self.config.executable_path}"
            logger.error(error_msg)
            raise MnamerError(error_msg)

        except Exception as e:
            error_msg = f"Error running mnamer: {e}"
            logger.error(error_msg)
            raise MnamerError(error_msg)

    def _parse_mnamer_output(self, output: str, original_path: str) -> Optional[str]:
        """
        Parse mnamer output to extract new filename.

        Args:
            output: mnamer stdout/stderr output.
            original_path: Original file path.

        Returns:
            New filename (basename only) or None if parsing fails.
        """
        try:
            # mnamer typically outputs something like:
            # "Original Name.mkv" -> "Renamed Name (2023).mkv"

            # Look for arrow pattern
            for line in output.split("\n"):
                if "->" in line or "→" in line:
                    # Extract the part after the arrow
                    if "->" in line:
                        parts = line.split("->")
                    else:
                        parts = line.split("→")

                    if len(parts) >= 2:
                        new_name = parts[-1].strip().strip('"').strip("'")
                        # Extract just the filename if it's a full path
                        new_name = os.path.basename(new_name)
                        return new_name

            # Alternative: look for "renamed to" pattern
            for line in output.split("\n"):
                if "renamed to" in line.lower():
                    # Try to extract filename
                    parts = line.lower().split("renamed to")
                    if len(parts) >= 2:
                        new_name = parts[-1].strip().strip('"').strip("'")
                        new_name = os.path.basename(new_name)
                        return new_name

            # If we can't parse output, return None
            logger.warning("Could not parse mnamer output to extract new filename")
            return None

        except Exception as e:
            logger.error(f"Error parsing mnamer output: {e}")
            return None

    def get_renamed_path(self, original_path: str, new_filename: str) -> str:
        """
        Construct full path with new filename.

        Args:
            original_path: Original file path.
            new_filename: New filename from mnamer.

        Returns:
            Full path with new filename in same directory.
        """
        directory = os.path.dirname(original_path)
        return os.path.join(directory, new_filename)
