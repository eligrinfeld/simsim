import time, os, glob
from fastapi.testclient import TestClient
from apps.event_dashboard import server as srv


def test_events_backfill_since(monkeypatch):
    # Prepare synthetic recent events
    srv.recent_events.clear()
    t0 = int(time.time())
    evt1 = {"type": "NewsBurst", "key": "SPY", "ts": t0, "data": {"count": 3, "window_sec": 120}}
    evt2 = {"type": "MacroShock", "key": "US:CPI", "ts": t0 + 10, "data": {"actual": 0.8, "estimate": 0.2, "surprise": 0.6}}
    srv.recent_events.append(evt1)
    srv.recent_events.append(evt2)

    with TestClient(srv.app) as client:
        r = client.get("/events")
        assert r.status_code == 200
        rows = r.json()
        # Should include both events
        types = [e["type"] for e in rows]
        assert "NewsBurst" in types and "MacroShock" in types

        r2 = client.get("/events", params={"since": t0})
        assert r2.status_code == 200
        rows2 = r2.json()
        # Should include only evt2 (ts > since)
        assert all(e["ts"] > t0 for e in rows2)
        assert any(e["type"] == "MacroShock" for e in rows2)


def test_event_dashboard_telemetry(tmp_path, monkeypatch):
    # Write logs under tmp
    monkeypatch.chdir(tmp_path)
    with TestClient(srv.app) as client:
        payload = {"cat": "pill", "action": "Breakout", "ts": int(time.time())}
        resp = client.post("/telemetry", json=payload)
        assert resp.status_code == 204
        files = glob.glob("data/telemetry/*.log")
        assert files, "Expected telemetry log file"
        content = open(files[0]).read()
        assert "Breakout" in content

