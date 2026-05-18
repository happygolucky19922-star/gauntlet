from fastapi.testclient import TestClient

from app.main import app
from app.system2.tools import SandboxedToolExecutor


client = TestClient(app)


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


def test_load_mock_and_chat() -> None:
    load = client.post("/models/load", json={"model_path": "mock://echo", "quantization": "awq"})
    assert load.status_code == 200

    chat = client.post(
        "/chat",
        json={"message": "hi lucy", "temperature": 0.1, "top_p": 0.8, "max_tokens": 128},
    )
    assert chat.status_code == 200
    payload = chat.json()
    assert "mock-model-reply" in payload["reply"]

    trace = client.get(f"/traces/{payload['trace_id']}")
    assert trace.status_code == 200
    assert "USER: hi lucy" in trace.json()["trace"]


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
    import app.main as main_app

    load = client.post("/models/load", json={"model_path": "mock://echo", "quantization": "awq"})
    assert load.status_code == 200

    def fail_if_system2_runs(*args, **kwargs):
        raise AssertionError("System-2 tools should not run when tools_enabled is false")

    def direct_generate(prompt, config=None):
        return f"FINAL: direct reply for {prompt}"

    monkeypatch.setattr(main_app.executive, "run", fail_if_system2_runs)
    monkeypatch.setattr(main_app.engine, "generate", direct_generate)

    chat = client.post("/chat", json={"message": "no tools", "tools_enabled": False})

    assert chat.status_code == 200
    payload = chat.json()
    assert payload["reply"] == "direct reply for no tools"

    trace = client.get(f"/traces/{payload['trace_id']}")
    assert trace.status_code == 200
    assert "USER: no tools" in trace.json()["trace"]
