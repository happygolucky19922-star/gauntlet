from __future__ import annotations

import json
import uuid

try:
    from chromadb import PersistentClient
except Exception:  # pragma: no cover - optional dependency fallback
    PersistentClient = None

from ..config import AppConfig
from ..inference.vllm_engine import GenerationConfig, VLLMEngine
from .tools import SandboxedToolExecutor


SYSTEM_PROMPT = """You are Lucy System-2 Executive.
Use ReAct format:
THOUGHT: concise reasoning
ACTION: {"tool":"xxd","args":["-l","64","/path/to/local/file"]}
OBSERVATION: command output summary
FINAL: final user response
Only use the allowlisted local tools; avoid network actions and shell interpreters.
"""


class System2Executive:
    def __init__(self, engine: VLLMEngine, config: AppConfig) -> None:
        self.engine = engine
        self.config = config
        self.executor = SandboxedToolExecutor(timeout_sec=config.max_tool_runtime_sec)
        self.collection = None
        self._in_memory_traces: dict[str, str] = {}
        if PersistentClient is not None:
            self.chroma = PersistentClient(path=str(config.chroma_dir))
            self.collection = self.chroma.get_or_create_collection("execution_traces")
        config.traces_dir.mkdir(parents=True, exist_ok=True)

    def _extract_action(self, text: str) -> dict | None:
        for line in text.splitlines():
            if not line.startswith("ACTION:"):
                continue
            raw = line.split("ACTION:", 1)[1].strip()
            try:
                action = json.loads(raw)
            except json.JSONDecodeError:
                return None
            if not isinstance(action, dict):
                return None
            return action
        return None

    def _persist_trace(self, trace_id: str, trace_text: str, source: str) -> None:
        trace_path = self.config.traces_dir / f"{trace_id}.log"
        trace_path.write_text(trace_text)
        self._in_memory_traces[trace_id] = trace_text

        if self.collection is not None:
            try:
                self.collection.add(
                    ids=[trace_id],
                    documents=[trace_text],
                    embeddings=[[0.0]],
                    metadatas=[{"source": source, "trace_path": str(trace_path)}],
                )
            except Exception:
                # Chroma persistence is best-effort; local trace files remain authoritative.
                self.collection = None

    def run(self, user_input: str, generation: GenerationConfig | None = None, max_steps: int = 5) -> tuple[str, str]:
        trace_id = str(uuid.uuid4())
        context = f"{SYSTEM_PROMPT}\nUSER: {user_input}\n"
        trace_lines: list[str] = [context]
        final = ""

        for _ in range(max_steps):
            model_out = self.engine.generate(context, config=generation)
            trace_lines.append(model_out)

            if "FINAL:" in model_out:
                final = model_out.split("FINAL:", 1)[1].strip()
                break

            action = self._extract_action(model_out)
            if not action:
                context += "\nOBSERVATION: invalid action format; provide JSON action."
                continue

            try:
                result = self.executor.run(action["tool"], action.get("args", []))
                observation = (
                    f"OBSERVATION:\nCMD={result.command}\nRC={result.returncode}\n"
                    f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}\n"
                )
            except Exception as exc:  # controlled conversion to observation
                observation = f"OBSERVATION: tool execution failed: {exc}"

            trace_lines.append(observation)
            context += f"\n{model_out}\n{observation}\n"

        trace_text = "\n".join(trace_lines)
        self._persist_trace(trace_id, trace_text, source="system2")

        return final or "No final answer produced.", trace_id


    def record_direct_response(self, user_input: str, model_out: str) -> str:
        trace_id = str(uuid.uuid4())
        trace_text = f"USER: {user_input}\n{model_out}"
        self._persist_trace(trace_id, trace_text, source="direct_chat")

        return trace_id

    def get_trace(self, trace_id: str) -> str:
        trace_path = self.config.traces_dir / f"{trace_id}.log"
        if trace_path.exists():
            return trace_path.read_text()
        if trace_id in self._in_memory_traces:
            return self._in_memory_traces[trace_id]
        raise KeyError(trace_id)
