import importlib.util
from fastapi.testclient import TestClient
import os


def load_app():
    spec = importlib.util.spec_from_file_location("stock_app", "apps/stock_analyzer/app.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_explain_fallback_when_no_api_key(monkeypatch):
    # Ensure OPENAI_API_KEY is not set
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    mod = load_app()
    client = TestClient(mod.app)

    payload = {
        "symbol": "AAPL",
        "factor_key": "valuation",
        "context": {"scores": {"valuation": 3.2}, "fundamentals": {"pe": 28.0}}
    }
    # Should return 400 per implementation when key missing
    resp = client.post("/explain", json=payload)
    assert resp.status_code in (200, 400)
    if resp.status_code == 400:
        assert "OPENAI_API_KEY" in resp.text
    else:
        data = resp.json()
        assert "explanation" in data


def test_news_proxy_handles_error(monkeypatch):
    # Point macro service to an invalid port to force error
    mod = load_app()
    client = TestClient(mod.app)

    # Monkeypatch httpx.AsyncClient.get to simulate failure
    import types
    async def fake_get(self, url, params=None):
        class Resp:
            status_code = 500
            text = "bad"
        return Resp()
    monkeypatch.setattr(mod.httpx.AsyncClient, "get", fake_get, raising=True)

    # Expect 500 from our proxy
    resp = client.get("/news", params={"ticker": "AAPL", "days": 7})
    assert resp.status_code == 500
    assert "Failed to fetch news" in resp.text

