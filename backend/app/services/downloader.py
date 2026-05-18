from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

import httpx

from ..config import AppConfig


class ModelDownloader:
    def __init__(self, config: AppConfig, download_root: Path | None = None) -> None:
        self.config = config
        self.download_root = download_root or Path.home() / "models" / "downloads"
        self.download_root.mkdir(parents=True, exist_ok=True)

    def from_huggingface(self, repo_id: str, filename: str) -> Path:
        if self.config.offline_mode:
            raise RuntimeError("Offline mode is enabled; remote download is disabled")
        if not repo_id.strip() or not filename.strip():
            raise RuntimeError("repo_id and filename are required")

        from huggingface_hub import hf_hub_download

        local_path = hf_hub_download(repo_id=repo_id, filename=filename, local_dir=str(self.download_root))
        return Path(local_path)

    def from_github_release(self, url: str, output_name: str) -> Path:
        if self.config.offline_mode:
            raise RuntimeError("Offline mode is enabled; remote download is disabled")

        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.netloc != "github.com":
            raise RuntimeError("Only https://github.com release URLs are allowed")
        if not output_name.strip() or Path(output_name).name != output_name:
            raise RuntimeError("output_name must be a simple file name")

        destination = self.download_root / output_name
        with httpx.stream("GET", url, follow_redirects=True, timeout=60.0) as response:
            response.raise_for_status()
            with destination.open("wb") as handle:
                for chunk in response.iter_bytes():
                    handle.write(chunk)
        return destination
