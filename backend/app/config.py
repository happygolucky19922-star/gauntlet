from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _env_flag(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


@dataclass(slots=True)
class AppConfig:
    model_scan_roots: list[Path] = field(
        default_factory=lambda: [
            Path("/media"),
            Path.home() / "models",
            Path("/mnt"),
        ]
    )
    cloud_mount_roots: list[Path] = field(default_factory=lambda: [Path(f"/run/user/{os.getuid()}/gvfs")])
    supported_extensions: tuple[str, ...] = (".gguf", ".safetensors")
    chroma_dir: Path = Path(os.getenv("LUCY_CHROMA_DIR", "./data/chroma"))
    traces_dir: Path = Path(os.getenv("LUCY_TRACES_DIR", "./data/traces"))
    runtime_state_path: Path = Path(os.getenv("LUCY_RUNTIME_STATE", "./data/runtime_settings.json"))
    offline_mode: bool = _env_flag("LUCY_OFFLINE_MODE", True)
    max_tool_runtime_sec: int = int(os.getenv("LUCY_TOOL_TIMEOUT", "30"))
    max_scan_depth: int = int(os.getenv("LUCY_SCAN_DEPTH", "6"))
    default_hardware_profile: str = os.getenv("LUCY_HW_PROFILE", "intel_core_ultra_7")

    def runtime_profile(self) -> dict[str, int | str]:
        """Conservative defaults optimized for Intel Core Ultra laptops.

        These defaults are intended for local/offline runs where iGPU memory and
        thermals are constrained.
        """
        if self.default_hardware_profile == "intel_core_ultra_7":
            return {
                "profile": "intel_core_ultra_7",
                "suggested_backend": "llama.cpp",
                "cpu_threads": 8,
                "context_length": 4096,
                "gpu_layers": 0,
                "batch_size": 256,
            }

        return {
            "profile": "generic",
            "suggested_backend": "vllm",
            "cpu_threads": 4,
            "context_length": 2048,
            "gpu_layers": 0,
            "batch_size": 128,
        }


DEFAULT_CONNECTORS = {
    "github": False,
    "web_search": False,
    "postgresql": False,
    "cloud_storage": False,
    "pure_local": True,
}
