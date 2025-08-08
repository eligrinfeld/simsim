import importlib.util


def test_macro_endpoint_ok_without_key():
  # If FRED_API_KEY isn't set, endpoint should not error and returns empty values
  spec = importlib.util.spec_from_file_location("data_app", "services/data_api/app.py")
  mod = importlib.util.module_from_spec(spec)
  assert spec.loader is not None
  spec.loader.exec_module(mod)

  from fastapi.testclient import TestClient

  client = TestClient(mod.app)
  resp = client.get("/macro", params={"series_id": "UNRATE"})
  assert resp.status_code == 200
  data = resp.json()
  assert data["series_id"] == "UNRATE"
  assert "values" in data

