from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from typing import Any


@dataclass(slots=True)
class GenerationConfig:
    temperature: float = 0.2
    max_tokens: int = 1024
    top_p: float = 0.9


class VLLMEngine:
    """Production local model engine for GGUF llama.cpp and vLLM models.

    Production callers must load an existing local model path. Tests patch this
    boundary explicitly instead of relying on a synthetic runtime path.
    """

    def __init__(self) -> None:
        self._engine: Any = None
        self._backend: str | None = None
        self._loaded_model_path: str | None = None
        self._lock = RLock()

    @property
    def loaded_model_path(self) -> str | None:
        return self._loaded_model_path

    @property
    def backend(self) -> str | None:
        return self._backend

    def load(
        self,
        model_path: str,
        quantization: str = "awq",
        *,
        n_ctx: int = 4096,
        n_threads: int = 8,
        n_gpu_layers: int = 0,
    ) -> None:
        path = Path(model_path).expanduser()
        if not path.exists():
            raise RuntimeError(f"Model path does not exist: {path}")

        with self._lock:
            if path.suffix.lower() == ".gguf":
                try:
                    from llama_cpp import Llama
                except ImportError as exc:  # pragma: no cover - depends on optional wheel availability
                    raise RuntimeError(
                        "GGUF models require llama-cpp-python. Install backend requirements first."
                    ) from exc

                self._engine = Llama(
                    model_path=str(path),
                    n_ctx=n_ctx,
                    n_threads=n_threads,
                    n_gpu_layers=n_gpu_layers,
                    verbose=False,
                )
                self._backend = "llama.cpp"
            else:
                try:
                    from vllm import LLM
                except ImportError as exc:  # pragma: no cover - depends on optional GPU stack availability
                    raise RuntimeError("vLLM models require the vllm package and a supported runtime.") from exc

                self._engine = LLM(model=str(path), quantization=quantization, trust_remote_code=False)
                self._backend = "vllm"

            self._loaded_model_path = str(path)

    def is_loaded(self) -> bool:
        with self._lock:
            return self._engine is not None

    def generate(self, prompt: str, config: GenerationConfig | None = None) -> str:
        with self._lock:
            if self._engine is None or self._backend is None:
                raise RuntimeError("No model is loaded.")

            cfg = config or GenerationConfig()
            if self._backend == "llama.cpp":
                output = self._engine(
                    prompt,
                    max_tokens=cfg.max_tokens,
                    temperature=cfg.temperature,
                    top_p=cfg.top_p,
                    echo=False,
                )
                return str(output["choices"][0]["text"])

            from vllm import SamplingParams

            sampling = SamplingParams(
                temperature=cfg.temperature,
                top_p=cfg.top_p,
                max_tokens=cfg.max_tokens,
            )
            outputs = self._engine.generate([prompt], sampling)
            return outputs[0].outputs[0].text
