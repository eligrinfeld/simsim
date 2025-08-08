import importlib.util, os, time
from fastapi.testclient import TestClient


def test_macro_cache_refresh_param():
  spec = importlib.util.spec_from_file_location("data_app", "services/data_api/app.py")
  mod = importlib.util.module_from_spec(spec)
  assert spec.loader is not None
  spec.loader.exec_module(mod)
  client = TestClient(mod.app)

  # First call (likely cache miss if no file yet)
  r1 = client.get("/macro", params={"series_id": "UNRATE", "ttl_seconds": 1})
  assert r1.status_code == 200
  # Second call uses cache if file exists
  r2 = client.get("/macro", params={"series_id": "UNRATE", "ttl_seconds": 9999})
  assert r2.status_code == 200
  # Force refresh should bypass cache codepath (cannot assert internal behavior, but should still return 200)
  r3 = client.get("/macro", params={"series_id": "UNRATE", "refresh": True})
  assert r3.status_code == 200

