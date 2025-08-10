import importlib.util
from fastapi.testclient import TestClient
import os, json, pathlib


def load_app(repo_root: pathlib.Path):
    spec = importlib.util.spec_from_file_location("stock_app", str(repo_root / "apps/stock_analyzer/app.py"))
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_precomputed_sector_percentiles_preferred(tmp_path, monkeypatch):
    # Prepare a temp data dir with a sector percentiles file for AAPL
    data_dir = tmp_path / "data" / "sector_percentiles"
    data_dir.mkdir(parents=True)
    payload = {
        "sector": "Information Technology",
        "as_of": "2025-08-10T00:00:00Z",
        "percentiles": {"valuation": 65, "growth": 72, "quality": 81},
    }
    with open(data_dir / "AAPL.json", "w") as f:
        json.dump(payload, f)

    # Ensure the app reads from this temp repo root
    repo_root = pathlib.Path(os.getcwd())
    try:
        # Create a minimal apps/stock_analyzer path in tmp to import the app from repo
        mod = load_app(repo_root)
        client = TestClient(mod.app)

        # Change CWD to tmp so the data dir is picked up
        monkeypatch.chdir(tmp_path)

        resp = client.get("/analyze", params={"ticker": "AAPL"})
        assert resp.status_code == 200
        data = resp.json()

        assert data["percentiles"] == payload["percentiles"]
        assert data["percentiles_meta"]["source"] == "precomputed"
        assert data["percentiles_meta"]["as_of"] == payload["as_of"]
    finally:
        pass

