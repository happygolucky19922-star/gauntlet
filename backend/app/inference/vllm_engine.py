from __future__ import annotations

from dataclasses import dataclass
from threading import RLock


@dataclass(slots=True)
class GenerationConfig:
    temperature: float = 0.2
    max_tokens: int = 1024
    top_p: float = 0.9


class VLLMEngine:
    """Thin wrapper around vLLM with optional mock mode for local development/testing."""

    def __init__(self) -> None:
        self._engine = None
        self._loaded_model_path: str | None = None
        self._mock_mode: bool = False
        self._lock = RLock()

    @property
    def loaded_model_path(self) -> str | None:
        return self._loaded_model_path

    def load(self, model_path: str, quantization: str = "awq") -> None:
        with self._lock:
            if model_path == "mock://echo":
                self._mock_mode = True
                self._engine = object()
                self._loaded_model_path = model_path
                return

            from vllm import LLM

            self._engine = LLM(model=model_path, quantization=quantization, trust_remote_code=False)
            self._loaded_model_path = model_path
            self._mock_mode = False

    def is_loaded(self) -> bool:
        with self._lock:
            return self._engine is not None

    def generate(self, prompt: str, config: GenerationConfig | None = None) -> str:
        with self._lock:
            if self._engine is None:
                raise RuntimeError("No model is loaded.")

            if self._mock_mode:
                return f"FINAL: [mock-model-reply] {prompt[-200:]}"

            from vllm import SamplingParams

            cfg = config or GenerationConfig()
            sampling = SamplingParams(
                temperature=cfg.temperature,
                top_p=cfg.top_p,
                max_tokens=cfg.max_tokens,
            )
            outputs = self._engine.generate([prompt], sampling)
            return outputs[0].outputs[0].text
