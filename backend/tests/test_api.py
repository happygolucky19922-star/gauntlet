from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

import app.main as main_app
from app.main import app
from app.system2.tools import SandboxedToolExecutor


client = TestClient(app)


def _install_test_engine(monkeypatch, reply: str = "FINAL: local test reply") -> None:
    monkeypatch.setattr(main_app.engine, "is_loaded", lambda: True)
    monkeypatch.setattr(main_app.engine, "generate", lambda prompt, config=None: reply)


def test_health() -> None:
    r = client.get("/health")
    assert r.status_code == 200
    payload = r.json()
    assert payload["status"] == "ok"


def test_runtime_settings_toggle() -> None:
    current = client.get("/runtime/settings")
    assert current.status_code == 200

    r = client.post("/runtime/settings", json={"offline_mode": False})
    assert r.status_code == 200
    assert r.json()["offline_mode"] is False

    reset = client.post("/runtime/settings", json={"offline_mode": True})
    assert reset.status_code == 200
    assert reset.json()["offline_mode"] is True


def test_runtime_profile() -> None:
    r = client.get("/runtime/profile")
    assert r.status_code == 200
    payload = r.json()
    assert payload["profile"]
    assert payload["cpu_threads"] > 0


def test_patent_profiles() -> None:
    r = client.get("/runtime/patent-profiles")
    assert r.status_code == 200
    payload = r.json()
    assert "dense_knowledge_distillation" in payload
    assert "nonlinear_quantization" in payload


def test_load_requires_real_model_path(tmp_path: Path) -> None:
    missing = tmp_path / "missing.gguf"
    load = client.post("/models/load", json={"model_path": str(missing), "quantization": "awq"})

    assert load.status_code == 400
    assert "does not exist" in load.json()["detail"]


def test_chat_with_loaded_engine(monkeypatch) -> None:
    _install_test_engine(monkeypatch, reply="FINAL: local model reply")

    chat = client.post(
        "/chat",
        json={"message": "hi lucy", "temperature": 0.1, "top_p": 0.8, "max_tokens": 128},
    )

    assert chat.status_code == 200
    payload = chat.json()
    assert payload["reply"] == "local model reply"

    trace = client.get(f"/traces/{payload['trace_id']}")
    assert trace.status_code == 200
    assert "USER: hi lucy" in trace.json()["trace"]


def test_analyze_file_reports_real_metadata() -> None:
    r = client.post(
        "/files/analyze",
        files={"file": ("notes.txt", b"hello\nlucy\n", "text/plain")},
    )

    assert r.status_code == 200
    payload = r.json()
    assert payload["filename"] == "notes.txt"
    assert payload["size"] == 11
    assert payload["line_count"] == 2
    assert len(payload["sha256"]) == 64
    assert "Preview: hello lucy" in payload["summary"]


def test_open_api_endpoints_use_keyless_clients(monkeypatch) -> None:
    monkeypatch.setattr(
        main_app.open_api_client,
        "wikipedia_search",
        lambda query, limit=5: [{"title": query, "snippet": "open encyclopedia", "url": "https://example.test"}],
    )
    monkeypatch.setattr(
        main_app.open_api_client,
        "open_meteo_forecast",
        lambda location: {"location": {"name": location}, "current": {"temperature_2m": 21}, "daily": {}},
    )
    monkeypatch.setattr(
        main_app.open_api_client,
        "arxiv_search",
        lambda query, limit=5: [{"title": query, "summary": "paper", "url": "https://arxiv.org/abs/1", "published": "2026-01-01"}],
    )

    search = client.get("/open/search", params={"query": "Lucy", "limit": 1})
    weather = client.get("/open/weather", params={"location": "New York"})
    arxiv = client.get("/open/arxiv", params={"query": "agents", "limit": 1})

    assert search.status_code == 200
    assert search.json()["results"][0]["title"] == "Lucy"
    assert weather.status_code == 200
    assert weather.json()["location"]["name"] == "New York"
    assert arxiv.status_code == 200
    assert arxiv.json()["results"][0]["summary"] == "paper"


def test_arena_bounds() -> None:
    missing = client.get("/arena/101")
    assert missing.status_code == 404

    ok = client.get("/arena/1")
    assert ok.status_code == 200
    assert ok.json()["category"]


def test_trace_not_found() -> None:
    missing = client.get("/traces/not-a-real-id")
    assert missing.status_code == 404


def test_sandbox_rejects_bash() -> None:
    executor = SandboxedToolExecutor()

    try:
        executor.run("bash", ["-lc", "echo unsafe"])
    except ValueError as exc:
        assert "not allowed" in str(exc)
    else:  # pragma: no cover - defensive assertion
        raise AssertionError("bash should not be allowed by the sandbox executor")


def test_chat_respects_tools_disabled(monkeypatch) -> None:
    _install_test_engine(monkeypatch, reply="FINAL: direct reply for no tools")

    def fail_if_system2_runs(*args, **kwargs):
        raise AssertionError("System-2 tools should not run when tools_enabled is false")

    monkeypatch.setattr(main_app.executive, "run", fail_if_system2_runs)

    chat = client.post("/chat", json={"message": "no tools", "tools_enabled": False})

    assert chat.status_code == 200
    payload = chat.json()
    assert payload["reply"] == "direct reply for no tools"

    trace = client.get(f"/traces/{payload['trace_id']}")
    assert trace.status_code == 200
    assert "USER: no tools" in trace.json()["trace"]
