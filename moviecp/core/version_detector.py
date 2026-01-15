"""Version detection for duplicate movies."""
import os
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import List, Optional, Tuple

from loguru import logger

from moviecp.config import VersionDetectionConfig
from moviecp.utils.exceptions import VersionDetectionError


class VersionDetector:
    """Detects existing versions of movies and determines version numbers."""

    def __init__(self, config: VersionDetectionConfig):
        """
        Initialize version detector.

        Args:
            config: Version detection configuration.
        """
        self.config = config

    def detect_version(
        self, filename: str, target_directory: str
    ) -> Tuple[str, int]:
        """
        Detect if movie exists and determine version number.

        Args:
            filename: Movie filename to check.
            target_directory: Directory to search for existing versions.

        Returns:
            Tuple of (versioned_filename, version_number).
            If no existing version, returns (original_filename, 1).

        Raises:
            VersionDetectionError: If detection fails.
        """
        if not self.config.enabled:
            logger.debug("Version detection is disabled")
            return filename, 1

        try:
            # Get list of existing files
            existing_files = self._list_directory(target_directory)

            # Check for exact match or similar files
            matches = self._find_matches(filename, existing_files)

            if not matches:
                logger.info(f"No existing versions found for: {filename}")
                return filename, 1

            # Determine highest version number
            highest_version = self._get_highest_version(filename, matches)

            # Generate versioned filename
            next_version = highest_version + 1
            versioned_filename = self._add_version_suffix(filename, next_version)

            logger.info(
                f"Existing versions found. New file will be: {versioned_filename} "
                f"(version {next_version})"
            )

            return versioned_filename, next_version

        except Exception as e:
            error_msg = f"Error detecting version for {filename}: {e}"
            logger.error(error_msg)
            raise VersionDetectionError(error_msg)

    def _list_directory(self, directory: str) -> List[str]:
        """
        List all files in directory.

        Args:
            directory: Directory path.

        Returns:
            List of filenames (basenames only).
        """
        try:
            if not os.path.exists(directory):
                logger.warning(f"Directory does not exist: {directory}")
                return []

            files = []
            for item in os.listdir(directory):
                full_path = os.path.join(directory, item)
                if os.path.isfile(full_path):
                    files.append(item)

            return files

        except Exception as e:
            logger.error(f"Error listing directory {directory}: {e}")
            return []

    def _find_matches(self, filename: str, existing_files: List[str]) -> List[str]:
        """
        Find matching files (exact or similar).

        Args:
            filename: Filename to match.
            existing_files: List of existing filenames.

        Returns:
            List of matching filenames.
        """
        matches = []

        # Get base name without extension and without existing version suffix
        base_name = self._get_base_name(filename)

        for existing_file in existing_files:
            existing_base_name = self._get_base_name(existing_file)

            # Check for exact match (ignoring version suffix)
            if base_name.lower() == existing_base_name.lower():
                matches.append(existing_file)
                continue

            # Check for similar match if enabled
            if self.config.check_similar:
                similarity = self._calculate_similarity(base_name, existing_base_name)
                if similarity >= self.config.similarity_threshold:
                    matches.append(existing_file)
                    logger.debug(
                        f"Found similar file: {existing_file} "
                        f"(similarity: {similarity:.2f})"
                    )

        return matches

    def _get_base_name(self, filename: str) -> str:
        """
        Get base name without extension and version suffix.

        Args:
            filename: Full filename.

        Returns:
            Base name.
        """
        # Remove extension
        name = Path(filename).stem

        # Remove version suffix if present
        version_pattern = self.config.format.replace("{number}", r"\d+")
        version_pattern = version_pattern.replace(".", r"\.")
        name = re.sub(version_pattern + r"$", "", name)

        return name.strip()

    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate similarity between two strings.

        Args:
            str1: First string.
            str2: Second string.

        Returns:
            Similarity ratio (0.0 to 1.0).
        """
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

    def _get_highest_version(self, filename: str, matches: List[str]) -> int:
        """
        Get highest version number from matching files.

        Args:
            filename: Original filename.
            matches: List of matching filenames.

        Returns:
            Highest version number found (0 if no versions found).
        """
        highest = 0

        for match in matches:
            version = self._extract_version_number(match)
            if version > highest:
                highest = version

        return highest

    def _extract_version_number(self, filename: str) -> int:
        """
        Extract version number from filename.

        Args:
            filename: Filename possibly containing version suffix.

        Returns:
            Version number (1 if no version suffix found).
        """
        # Create regex pattern from config format
        # e.g., ".v{number}" becomes r"\.v(\d+)"
        pattern = self.config.format.replace("{number}", r"(\d+)")
        pattern = pattern.replace(".", r"\.")

        # Search for pattern in filename
        match = re.search(pattern, filename)

        if match:
            try:
                version = int(match.group(1))
                return version
            except (ValueError, IndexError):
                pass

        # No version suffix found, assume version 1
        return 1

    def _add_version_suffix(self, filename: str, version: int) -> str:
        """
        Add version suffix to filename.

        Args:
            filename: Original filename.
            version: Version number to add.

        Returns:
            Filename with version suffix.
        """
        # Split filename and extension
        name, ext = os.path.splitext(filename)

        # Generate version suffix
        version_suffix = self.config.format.replace("{number}", str(version))

        # Construct versioned filename
        versioned_filename = f"{name}{version_suffix}{ext}"

        return versioned_filename
