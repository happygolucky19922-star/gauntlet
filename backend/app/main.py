from __future__ import annotations

import json
from dataclasses import asdict

from fastapi import FastAPI, File, HTTPException, UploadFile

from .config import AppConfig, DEFAULT_CONNECTORS
from .inference.vllm_engine import GenerationConfig, VLLMEngine
from .model_manager import ModelManager
from .optimization.patent_profiles import patent_profiles
from .schemas import (
    ChatRequest,
    ChatResponse,
    ConnectorState,
    FileAnalyzeResponse,
    LoadModelRequest,
    ModelInfo,
    OpenSearchResponse,
    RuntimeProfile,
    RuntimeSettings,
    WeatherResponse,
)
from .services.downloader import ModelDownloader
from .services.file_analyzer import analyze_upload
from .services.open_apis import OpenAPIClient
from .system2.executive import System2Executive
from .test_arena import TestArena

app = FastAPI(title="Lucy Backend", version="0.2.0")

config = AppConfig()
model_manager = ModelManager(config)
engine = VLLMEngine()
executive = System2Executive(engine=engine, config=config)
downloader = ModelDownloader(config=config)
open_api_client = OpenAPIClient()
arena = TestArena()
connectors = ConnectorState(**DEFAULT_CONNECTORS)


def _load_runtime_settings() -> None:
    if not config.runtime_state_path.exists():
        return
    try:
        data = json.loads(config.runtime_state_path.read_text())
    except json.JSONDecodeError:
        return
    config.offline_mode = bool(data.get("offline_mode", config.offline_mode))


def _save_runtime_settings() -> None:
    config.runtime_state_path.parent.mkdir(parents=True, exist_ok=True)
    config.runtime_state_path.write_text(json.dumps({"offline_mode": config.offline_mode}, indent=2))


_load_runtime_settings()


@app.get("/health")
def health() -> dict[str, str | bool]:
    return {"status": "ok", "offline_mode": config.offline_mode, "model_loaded": engine.is_loaded()}


@app.get("/runtime/profile", response_model=RuntimeProfile)
def get_runtime_profile() -> RuntimeProfile:
    return RuntimeProfile(**config.runtime_profile())


@app.get("/runtime/patent-profiles")
def get_patent_profiles() -> dict[str, dict[str, object]]:
    return patent_profiles()


@app.get("/runtime/settings", response_model=RuntimeSettings)
def get_runtime_settings() -> RuntimeSettings:
    return RuntimeSettings(offline_mode=config.offline_mode)


@app.post("/runtime/settings", response_model=RuntimeSettings)
def set_runtime_settings(settings: RuntimeSettings) -> RuntimeSettings:
    config.offline_mode = settings.offline_mode
    _save_runtime_settings()
    return RuntimeSettings(offline_mode=config.offline_mode)


@app.get("/models", response_model=list[ModelInfo])
def list_models() -> list[ModelInfo]:
    return model_manager.discover_models()


@app.post("/models/load")
def load_model(req: LoadModelRequest) -> dict[str, str]:
    try:
        engine.load(
            req.model_path,
            quantization=req.quantization,
            n_ctx=req.n_ctx,
            n_threads=req.n_threads,
            n_gpu_layers=req.n_gpu_layers,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"loaded": req.model_path, "quantization": req.quantization, "backend": engine.backend or "unknown"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    if req.model_path and req.model_path != engine.loaded_model_path:
        try:
            engine.load(req.model_path)
        except RuntimeError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not engine.is_loaded():
        raise HTTPException(status_code=400, detail="No model loaded. Call /models/load first.")

    generation = GenerationConfig(
        temperature=req.temperature,
        top_p=req.top_p,
        max_tokens=req.max_tokens,
    )

    try:
        if req.tools_enabled:
            reply, trace_id = executive.run(req.message, generation=generation)
        else:
            model_out = engine.generate(req.message, config=generation)
            reply = model_out.split("FINAL:", 1)[1].strip() if "FINAL:" in model_out else model_out.strip()
            trace_id = executive.record_direct_response(req.message, model_out)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ChatResponse(reply=reply or "No response produced.", trace_id=trace_id)


@app.get("/traces/{trace_id}")
def get_trace(trace_id: str) -> dict[str, str]:
    try:
        trace = executive.get_trace(trace_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Trace not found") from exc
    return {"trace_id": trace_id, "trace": trace}


@app.get("/arena/{level}")
def get_arena_level(level: int) -> dict:
    if level < 1 or level > 100:
        raise HTTPException(status_code=404, detail="Level out of range")
    arena_level = arena.get_level(level)
    return asdict(arena_level)


@app.get("/connectors", response_model=ConnectorState)
def get_connectors() -> ConnectorState:
    return connectors


@app.post("/connectors", response_model=ConnectorState)
def set_connectors(new_state: ConnectorState) -> ConnectorState:
    global connectors
    if config.offline_mode and (new_state.github or new_state.web_search or new_state.cloud_storage):
        raise HTTPException(status_code=400, detail="Offline mode forbids network-enabled connectors")
    connectors = new_state
    return connectors


@app.post("/files/analyze", response_model=FileAnalyzeResponse)
async def analyze_file(file: UploadFile = File(...)) -> FileAnalyzeResponse:
    payload = await file.read()
    analysis = analyze_upload(file.filename, payload, file.content_type)
    return FileAnalyzeResponse(**asdict(analysis))


@app.get("/open/search", response_model=OpenSearchResponse)
def open_search(query: str, limit: int = 5) -> OpenSearchResponse:
    try:
        results = open_api_client.wikipedia_search(query=query, limit=max(1, min(limit, 10)))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return OpenSearchResponse(results=results)


@app.get("/open/weather", response_model=WeatherResponse)
def open_weather(location: str) -> WeatherResponse:
    try:
        forecast = open_api_client.open_meteo_forecast(location=location)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return WeatherResponse(**forecast)


@app.get("/open/arxiv", response_model=OpenSearchResponse)
def open_arxiv(query: str, limit: int = 5) -> OpenSearchResponse:
    try:
        results = open_api_client.arxiv_search(query=query, limit=max(1, min(limit, 10)))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return OpenSearchResponse(results=results)


@app.post("/models/download/hf")
def download_model_hf(repo_id: str, filename: str) -> dict[str, str]:
    try:
        path = downloader.from_huggingface(repo_id=repo_id, filename=filename)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"downloaded": str(path)}


@app.post("/models/download/github")
def download_model_github(url: str, output_name: str) -> dict[str, str]:
    try:
        path = downloader.from_github_release(url=url, output_name=output_name)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"downloaded": str(path)}
