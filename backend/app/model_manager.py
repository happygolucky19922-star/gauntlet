from __future__ import annotations

import os
from pathlib import Path
import psutil

from .config import AppConfig
from .schemas import ModelInfo


class ModelManager:
    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def _iter_mount_points(self) -> set[Path]:
        mounts: set[Path] = set()
        for partition in psutil.disk_partitions(all=False):
            mounts.add(Path(partition.mountpoint))

        for root in [*self.config.model_scan_roots, *self.config.cloud_mount_roots]:
            if root.exists() and root.is_dir():
                mounts.add(root)
        return mounts

    def _walk_with_depth(self, root: Path):
        root_depth = len(root.parts)
        for current_root, dirs, files in os.walk(root):
            current_path = Path(current_root)
            depth = len(current_path.parts) - root_depth
            if depth >= self.config.max_scan_depth:
                dirs[:] = []
            yield current_path, files

    def discover_models(self) -> list[ModelInfo]:
        discovered: dict[str, ModelInfo] = {}

        for mount in self._iter_mount_points():
            if not mount.exists() or not mount.is_dir():
                continue

            for current_dir, files in self._walk_with_depth(mount):
                for file_name in files:
                    model_path = current_dir / file_name
                    ext = model_path.suffix.lower()
                    if ext not in self.config.supported_extensions:
                        continue

                    try:
                        stat = model_path.stat()
                    except OSError:
                        continue

                    source = "usb_or_media" if str(model_path).startswith("/media/") else "local"
                    discovered[str(model_path)] = ModelInfo(
                        name=model_path.stem,
                        path=str(model_path),
                        size_bytes=stat.st_size,
                        format=ext.removeprefix("."),
                        source=source,
                    )

        return sorted(discovered.values(), key=lambda m: m.size_bytes, reverse=True)
