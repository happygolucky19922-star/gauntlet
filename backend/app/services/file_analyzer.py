from __future__ import annotations

import hashlib
import string
from dataclasses import dataclass
from pathlib import PurePath


@dataclass(slots=True)
class FileAnalysis:
    filename: str
    size: int
    sha256: str
    media_type: str
    line_count: int | None
    summary: str


_TEXT_CHARS = set(bytes(string.printable, "ascii")) | {9, 10, 13}


def _is_probably_text(payload: bytes) -> bool:
    if not payload:
        return True
    sample = payload[:4096]
    textish = sum(byte in _TEXT_CHARS for byte in sample)
    return (textish / len(sample)) > 0.90


def analyze_upload(filename: str | None, payload: bytes, content_type: str | None = None) -> FileAnalysis:
    safe_name = PurePath(filename or "unknown").name or "unknown"
    digest = hashlib.sha256(payload).hexdigest()
    size = len(payload)

    if _is_probably_text(payload):
        decoded = payload.decode("utf-8", errors="replace")
        lines = decoded.splitlines()
        non_empty = [line.strip() for line in lines if line.strip()]
        preview = " ".join(non_empty[:3])[:240]
        media_type = content_type or "text/plain"
        summary = (
            f"Text file '{safe_name}' with {len(lines)} lines, {size} bytes, "
            f"sha256={digest}. Preview: {preview or '[empty file]'}"
        )
        return FileAnalysis(
            filename=safe_name,
            size=size,
            sha256=digest,
            media_type=media_type,
            line_count=len(lines),
            summary=summary,
        )

    media_type = content_type or "application/octet-stream"
    summary = f"Binary file '{safe_name}' with {size} bytes, sha256={digest}, media_type={media_type}."
    return FileAnalysis(
        filename=safe_name,
        size=size,
        sha256=digest,
        media_type=media_type,
        line_count=None,
        summary=summary,
    )
