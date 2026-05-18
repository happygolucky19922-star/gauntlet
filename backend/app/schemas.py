from __future__ import annotations

from pydantic import BaseModel, Field


class ModelInfo(BaseModel):
    name: str
    path: str
    size_bytes: int
    format: str
    source: str = "local"


class LoadModelRequest(BaseModel):
    model_path: str
    quantization: str = "awq"
    n_ctx: int = Field(default=4096, ge=512, le=131072)
    n_threads: int = Field(default=8, ge=1, le=256)
    n_gpu_layers: int = Field(default=0, ge=0, le=999)


class ChatRequest(BaseModel):
    model_path: str | None = None
    message: str = Field(min_length=1)
    session_id: str = "default"
    tools_enabled: bool = True
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    max_tokens: int = Field(default=1024, ge=1, le=8192)


class ChatResponse(BaseModel):
    reply: str
    trace_id: str


class ArenaLevelResult(BaseModel):
    level: int
    category: str
    passed: bool
    score: float
    details: str


class ConnectorState(BaseModel):
    github: bool = False
    web_search: bool = False
    postgresql: bool = False
    cloud_storage: bool = False
    pure_local: bool = True


class FileAnalyzeResponse(BaseModel):
    filename: str
    size: int
    sha256: str
    media_type: str
    line_count: int | None = None
    summary: str


class OpenSearchResponse(BaseModel):
    results: list[dict[str, str]]


class WeatherResponse(BaseModel):
    location: dict[str, object]
    current: dict[str, object]
    daily: dict[str, object]


class RuntimeSettings(BaseModel):
    offline_mode: bool = True


class RuntimeProfile(BaseModel):
    profile: str
    suggested_backend: str
    cpu_threads: int
    context_length: int
    gpu_layers: int
    batch_size: int
