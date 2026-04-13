from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class ToolResult:
    tool: str
    command: str
    stdout: str
    stderr: str
    returncode: int


class SandboxedToolExecutor:
    """Allowlisted local executor for analysis tasks."""

    ALLOWED_TOOLS = {"bash", "gdb", "tcpdump", "xxd", "hexdump"}
    BLOCKED_PATTERNS = ("curl ", "wget ", "nc ", "ncat ", "ssh ", "scp ")

    def __init__(self, timeout_sec: int = 30, cwd: Path | None = None) -> None:
        self.timeout_sec = timeout_sec
        self.cwd = cwd

    def run(self, tool: str, args: list[str]) -> ToolResult:
        if tool not in self.ALLOWED_TOOLS:
            raise ValueError(f"Tool {tool} is not allowed")

        rendered_cmd = " ".join([tool, *args])
        for pattern in self.BLOCKED_PATTERNS:
            if pattern in rendered_cmd:
                raise ValueError("Command contains blocked network pattern")

        completed = subprocess.run(
            [tool, *args],
            capture_output=True,
            text=True,
            timeout=self.timeout_sec,
            cwd=str(self.cwd) if self.cwd else None,
        )
        return ToolResult(
            tool=tool,
            command=rendered_cmd,
            stdout=completed.stdout,
            stderr=completed.stderr,
            returncode=completed.returncode,
        )
