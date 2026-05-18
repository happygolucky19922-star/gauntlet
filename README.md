# Gauntlet / Lucy (Operational Backend + Desktop Bridge Scaffold)

Lucy now ships an operational local-first backend with working API flows for:

- model discovery (`.gguf`, `.safetensors`) across mounts
- real local model loading and chat execution with GGUF llama.cpp or vLLM-compatible models
- System-2 ReAct loop with local tool execution and trace persistence
- 100-level gauntlet matrix API
- connector state management with offline enforcement
- file upload analysis endpoint for chat attachment workflows
- optional model download endpoints (Hugging Face / GitHub) when offline mode is disabled
- keyless free/open public API connectors for Wikipedia search, Open-Meteo weather, and arXiv search
- runtime profile hints for Intel Core Ultra 7 laptops

## Safety boundary

This project is for **defensive testing, benchmarking, and local experimentation**. It must not be used for unauthorized exploitation, malware, or illegal evasion workflows.

## Quick start

```bash
git clone https://github.com/happygolucky19922-star/gauntlet.git
cd gauntlet
./scripts/run_backend.sh
```

For a one-command install from GitHub into `~/.local/share/lucy/source`:

```bash
curl -fsSL https://raw.githubusercontent.com/happygolucky19922-star/gauntlet/main/scripts/install_from_github.sh | bash
```

To start immediately after downloading, run:

```bash
curl -fsSL https://raw.githubusercontent.com/happygolucky19922-star/gauntlet/main/scripts/install_from_github.sh | LUCY_START_AFTER_INSTALL=1 bash
```


### Dependency profiles

`backend/requirements.txt` contains the API server and keyless open-data integrations, so `scripts/run_backend.sh` can start the app from a fresh GitHub clone. Install optional model runtimes when you need them: set `LUCY_INSTALL_LLAMA=1` for GGUF/llama.cpp support, or set `LUCY_INSTALL_VLLM=1` for compatible GPU/server vLLM environments.

### Local smoke-test using a real local model

Download or place a free/open GGUF model on disk, install the GGUF runtime with `LUCY_INSTALL_LLAMA=1 ./scripts/run_backend.sh`, then load it by absolute path:

```bash
curl -X POST http://127.0.0.1:8000/models/load \
  -H 'content-type: application/json' \
  -d '{"model_path":"/home/user/models/model.gguf","n_ctx":4096,"n_threads":8,"n_gpu_layers":0}'

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
- `GET /open/search` (Wikipedia, keyless)
- `GET /open/weather` (Open-Meteo, keyless)
- `GET /open/arxiv` (arXiv, keyless)
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

## Tauri invoke handler

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

## Install from your GitHub repository

The installer is repo-aware and can target your fork or branch without changing the script:

```bash
curl -fsSL https://raw.githubusercontent.com/your-github-user/gauntlet/main/scripts/install_from_github.sh | \
  LUCY_GITHUB_REPO=your-github-user/gauntlet LUCY_GITHUB_REF=main bash
```

If you publish a tag such as `v0.1.0`, GitHub Actions builds `dist/lucy-build-*.tar.gz` and attaches it to the GitHub Release. You can also run the **Package Lucy release** workflow manually from the Actions tab to download the packaged artifact.

## Build packaging + download to laptop

1) Create a full build archive:

```bash
bash scripts/package_build.sh
```

2) Download from your laptop (single command pattern):

```bash
scp <server_user>@<server_host>:/workspace/gauntlet/dist/lucy-build-*.tar.gz ~/Downloads/
```

## Free/open API connectors

Lucy exposes keyless public API endpoints that do not require paid accounts or proprietary API keys:

```bash
curl "http://127.0.0.1:8000/open/search?query=local%20AI&limit=3"
curl "http://127.0.0.1:8000/open/weather?location=New%20York"
curl "http://127.0.0.1:8000/open/arxiv?query=agentic%20reasoning&limit=3"
```

These endpoints use Wikipedia, Open-Meteo, and arXiv respectively.
