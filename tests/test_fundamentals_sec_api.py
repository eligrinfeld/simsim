import importlib.util
import sys
import types
from fastapi.testclient import TestClient


class _FakeQueryApi:
  def __init__(self, api_key: str):
    self.api_key = api_key
  def get_filings(self, query):
    return {
      "filings": [
        {"formType": "10-Q", "filedAt": "2025-08-01", "companyName": "ACME", "cik": "0000000000", "linkToFilingDetails": "http://example"},
        {"formType": "10-K", "filedAt": "2025-02-01", "companyName": "ACME", "cik": "0000000000", "linkToFilingDetails": "http://example2"},
      ]
    }


def test_fundamentals_with_sec_key(monkeypatch):
  # Inject fake sec_api module so we don't rely on external package
  fake_mod = types.ModuleType("sec_api")
  fake_mod.QueryApi = _FakeQueryApi
  sys.modules["sec_api"] = fake_mod

  # Load the app module
  spec = importlib.util.spec_from_file_location("data_app", "services/data_api/app.py")
  mod = importlib.util.module_from_spec(spec)
  assert spec.loader is not None

  # Ensure the app can see SEC_API_KEY
  monkeypatch.setenv("SEC_API_KEY", "DUMMY")
  spec.loader.exec_module(mod)

  client = TestClient(mod.app)
  resp = client.get("/fundamentals", params={"ticker": "AAPL"})
  assert resp.status_code == 200
  data = resp.json()
  assert data["ticker"] == "AAPL"
  f = data.get("fundamentals", {})
  assert isinstance(f, dict)
  assert "sec_filings" in f
  assert isinstance(f["sec_filings"], list)
  assert len(f["sec_filings"]) == 2
  assert "formType" in f["sec_filings"][0]


def test_fundamentals_without_sec_key(monkeypatch):
  # Remove SEC_API_KEY and ensure we return empty fundamentals dict
  monkeypatch.delenv("SEC_API_KEY", raising=False)
  spec = importlib.util.spec_from_file_location("data_app", "services/data_api/app.py")
  mod = importlib.util.module_from_spec(spec)
  assert spec.loader is not None
  spec.loader.exec_module(mod)

  # Ensure .env fallback is ignored for this test
  monkeypatch.setattr(mod, "_get_env_var", lambda name: None)

  from fastapi.testclient import TestClient
  client = TestClient(mod.app)
  resp = client.get("/fundamentals", params={"ticker": "AAPL"})
  assert resp.status_code == 200
  data = resp.json()
  assert data["ticker"] == "AAPL"
  assert data.get("fundamentals", {}) == {}

