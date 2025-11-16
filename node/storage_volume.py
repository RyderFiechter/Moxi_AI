"""
Helpers for managing the encrypted storage backing file / mount path.
This module keeps file handling logic isolated from node/node_api.
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import Dict, Optional

BYTES_PER_GB = 1024 ** 3
DEFAULT_BACKING_DIR = Path("/var/moxi-node")
DEFAULT_BACKING_FILENAME = "storage-node.img"



class StorageVolumeManager:
    """Manage the encrypted backing file that reserves capacity for the node."""

    def __init__(
        self,
        mount_path: str,
        backing_file: Optional[str] = None,
        mapper_name: Optional[str] = None,
    ) -> None:
        self.mount_path = Path(mount_path).expanduser()
        if backing_file:
            self.backing_file = Path(backing_file).expanduser()
        elif os.name != "nt":
            self.backing_file = DEFAULT_BACKING_DIR / DEFAULT_BACKING_FILENAME
        else:
            # Default to a hidden file in the mount path for Windows environments
            self.backing_file = self.mount_path / ".moxi_encrypted.bin"
        self.mapper_name = mapper_name or "moxi-node"

    def _ensure_directories(self) -> None:
        """Create mount/backing directories if they do not exist."""
        try:
            if not self.mount_path.exists():
                self.mount_path.mkdir(parents=True, exist_ok=True)
        except PermissionError as exc:
            raise PermissionError(
                f"Cannot create mount path '{self.mount_path}'. "
                "Run the node with elevated permissions or pre-create the directory."
            ) from exc

        backing_parent = self.backing_file.parent
        try:
            if not backing_parent.exists():
                backing_parent.mkdir(parents=True, exist_ok=True)
        except PermissionError as exc:
            raise PermissionError(
                f"Cannot create backing directory '{backing_parent}'. "
                "Create it manually (e.g. `sudo mkdir -p /var/moxi-node && sudo chown $USER /var/moxi-node`)."
            ) from exc

    def _current_size_bytes(self) -> int:
        """Return the current size of the encrypted backing file."""
        try:
            return self.backing_file.stat().st_size
        except FileNotFoundError:
            return 0

    def _describe(self, message: str) -> Dict[str, object]:
        """Return metadata about the current volume state."""
        size_bytes = self._current_size_bytes()
        size_gb = round(size_bytes / BYTES_PER_GB, 4)
        return {
            "message": message,
            "mount_path": str(self.mount_path),
            "backing_file": str(self.backing_file),
            "mapper_name": self.mapper_name,
            "size_bytes": size_bytes,
            "size_gb": size_gb,
        }

    def initialize_volume(self) -> Dict[str, object]:
        """
        Ensure the mount path/backing file exists. Does not reserve space yet.
        """
        self._ensure_directories()
        if not self.backing_file.exists():
            with open(self.backing_file, "wb"):
                pass
        return self._describe("Encrypted backing file initialized.")

    def reserve_storage(self, storage_gb: float) -> Dict[str, object]:
        """
        Resize the backing file so it locks up storage_gb of capacity.

        Args:
            storage_gb: Amount of storage to reserve.
        """
        if storage_gb < 0:
            raise ValueError("Storage amount must be non-negative")

        self._ensure_directories()
        size_bytes = int(storage_gb * BYTES_PER_GB)
        with open(self.backing_file, "a+b") as volume_file:
            volume_file.truncate(size_bytes)

        return self._describe(
            f"Reserved {storage_gb:.2f} GB in encrypted backing file."
        )

    def release_storage(self) -> Dict[str, object]:
        """Remove the backing file entirely when releasing storage."""
        self._ensure_directories()
        if self.backing_file.exists():
            try:
                self.backing_file.unlink()
            except OSError as exc:
                raise RuntimeError(f"Failed to delete backing file: {exc}") from exc
        return self._describe("Deleted encrypted backing file.")

    def describe(self) -> Dict[str, object]:
        """Return metadata without mutating the backing file."""
        if not self.backing_file.exists():
            return self._describe("Encrypted backing file not created yet.")
        return self._describe("Encrypted backing file ready.")
