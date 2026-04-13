from fastapi.testclient import TestClient

from app.main import app


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
