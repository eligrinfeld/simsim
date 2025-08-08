import importlib.util


def test_fundamentals_endpoint_shape():
  # Skip if yfinance is missing in the environment (Data API depends on it)
  try:
    import yfinance  # noqa: F401
  except Exception:
    return

  spec = importlib.util.spec_from_file_location("data_app", "services/data_api/app.py")
  mod = importlib.util.module_from_spec(spec)
  assert spec.loader is not None
  spec.loader.exec_module(mod)

  from fastapi.testclient import TestClient

  client = TestClient(mod.app)
  # This should work even without SEC_API_KEY or sec_api installed, returning empty fundamentals
  resp = client.get("/fundamentals", params={"ticker": "AAPL"})
  assert resp.status_code == 200
  data = resp.json()
  assert data["ticker"] == "AAPL"
  assert "fundamentals" in data
  # If sec_api is missing, fundamentals is empty dict. If installed and key set, expect sec_filings key.
  assert isinstance(data["fundamentals"], dict)

