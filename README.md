# Gauntlet / Lucy (Operational Backend + Desktop Bridge Scaffold)

Lucy now ships an operational local-first backend with working API flows for:

- model discovery (`.gguf`, `.safetensors`) across mounts
- model loading and chat execution
- System-2 ReAct loop with local tool execution and trace persistence
- 100-level gauntlet matrix API
- connector state management with offline enforcement
- file upload analysis endpoint for chat attachment workflows
- optional model download endpoints (Hugging Face / GitHub) when offline mode is disabled
- runtime profile hints for Intel Core Ultra 7 laptops

## Safety boundary

This project is for **defensive testing, benchmarking, and local experimentation**. It must not be used for unauthorized exploitation, malware, or illegal evasion workflows.

## Quick start

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Local smoke-test using mock engine

```bash
curl -X POST http://127.0.0.1:8000/models/load \
  -H 'content-type: application/json' \
  -d '{"model_path":"mock://echo","quantization":"awq"}'

curl -X POST http://127.0.0.1:8000/chat \
  -H 'content-type: application/json' \
  -d '{"message":"hello from lucy", "temperature":0.2, "top_p":0.9, "max_tokens":256}'
```

Then inspect the saved System-2 trace:

```bash
curl http://127.0.0.1:8000/traces/<trace_id>
```

## Key endpoints

- `GET /health`
- `GET /runtime/profile`
- `GET /runtime/patent-profiles`
- `GET /runtime/settings`
- `POST /runtime/settings`
- `GET /models`
- `POST /models/load`
- `POST /chat`
- `GET /traces/{trace_id}`
- `GET /arena/{level}`
- `GET /connectors`
- `POST /connectors`
- `POST /files/analyze`
- `POST /models/download/hf`
- `POST /models/download/github`

## Offline toggle

Set `LUCY_OFFLINE_MODE=true` (default) to hard-disable remote connector/download features.

You can also toggle this while running:

```bash
curl -X POST http://127.0.0.1:8000/runtime/settings \
  -H 'content-type: application/json' \
  -d '{"offline_mode":false}'
```

Set back to offline:

```bash
curl -X POST http://127.0.0.1:8000/runtime/settings \
  -H 'content-type: application/json' \
  -d '{"offline_mode":true}'
```

## Intel Core Ultra 7 defaults

`GET /runtime/profile` returns conservative settings intended for Intel Core Ultra 7:

- `suggested_backend`: `llama.cpp`
- `cpu_threads`: `8`
- `context_length`: `4096`
- `gpu_layers`: `0` (CPU first stability)

## Patent-inspired local profiles

Use `GET /runtime/patent-profiles` to retrieve built-in profile templates for:

Patent reference mapping is documented in `PATENTS.md`.

- dense knowledge distillation style weighting
- non-linear quantization bucket allocation

You can also apply these from CLI during local training:

```bash
python scripts/lucy.py train --config /path/to/train_config.json --use-dkd --use-nlq
```

## Lucy evolution utility

```bash
python scripts/lucy.py convert --converter /path/to/convert.py --model-dir /models/hf --out /models/out/model.gguf
python scripts/lucy.py train --config /path/to/train_config.json
```

## Tauri invoke handler scaffold

See `tauri/src-tauri/src/main.rs` for:

- `start_model` with launch options (`threads`, `context_length`, `gpu_layers`)
- `stop_model`
- `model_status`
- `send_prompt`

The Tauri commands are now pre-tuned for local Intel laptop defaults (8 threads, 4096 context, CPU-first).

## One-click desktop launcher (Linux)

Install a local `.desktop` launcher with icon support:

```bash
bash scripts/install_desktop.sh
```

The launcher is placed in `~/.local/share/applications/lucy.desktop` and starts the local backend.

## Build packaging + download to laptop

1) Create a full build archive:

```bash
bash scripts/package_build.sh
```

2) Download from your laptop (single command pattern):

```bash
scp <server_user>@<server_host>:/workspace/gauntlet/dist/lucy-build-*.tar.gz ~/Downloads/
```
