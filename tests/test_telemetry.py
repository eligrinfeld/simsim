import importlib.util, pathlib, os
from fastapi.testclient import TestClient


def load_app(repo_root: pathlib.Path):
    spec = importlib.util.spec_from_file_location("stock_app", str(repo_root / "apps/stock_analyzer/app.py"))
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_telemetry_endpoint_accepts_payload(tmp_path, monkeypatch):
    # Ensure logs go to tmp by changing to it AFTER loading the app from repo root
    import os as _os
    repo_root = pathlib.Path(_os.getcwd())
    mod = load_app(repo_root)
    client = TestClient(mod.app)

    monkeypatch.chdir(tmp_path)

    payload = {"cat": "explain", "action": "open", "label": "valuation"}
    resp = client.post("/telemetry", json=payload)
    assert resp.status_code == 204

    # Verify a log line was created
    import glob, os
    files = glob.glob("data/telemetry/*.log")
    assert files, "Expected a telemetry log file to be created"
    content = open(files[0]).read()
    assert "explain" in content and "valuation" in content

