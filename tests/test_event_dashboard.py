import time
from fastapi.testclient import TestClient

# Import the server app and CEP utilities
from apps.event_dashboard import server as srv


def test_candles_seed_nonempty():
    # Use lifespan context so startup tasks run
    with TestClient(srv.app) as client:
        data = []
        # Poll up to ~3s for seed to appear
        for _ in range(60):
            r = client.get("/candles")
            assert r.status_code == 200
            data = r.json()
            if data:
                break
            time.sleep(0.05)
        assert isinstance(data, list) and len(data) > 0
        k = data[-1]
        for f in ["time", "open", "high", "low", "close"]:
            assert f in k


def test_ws_receives_bar():
    with TestClient(srv.app) as client:
        with client.websocket_connect("/ws") as ws:
            # Expect a Bar or any event within a short timeout
            msg = ws.receive_json()
            assert isinstance(msg, dict)
            assert msg.get("type") in {"Bar", "Breakout", "NewsBurst", "MacroShock", "TradeEntryIntent"}


def test_cep_emit_news_burst():
    cep = srv.CEP()
    emitted = []
    cep.sink.subscribe(lambda e: emitted.append(e))

    # Register sliding count rule to emit NewsBurst
    cep.on_sliding_count(
        name="test_news_burst",
        event_type="NewsItem",
        within_sec=120,
        threshold=3,
        where=lambda n: n.data.get("sentiment", 0) >= 0.6,
        emit_type="NewsBurst",
    )

    t0 = time.time()
    e1 = srv.Event("NewsItem", ts=t0, key="SPY", data={"sentiment": 0.7, "headline": "A"})
    e2 = srv.Event("NewsItem", ts=t0 + 1, key="SPY", data={"sentiment": 0.8, "headline": "B"})
    e3 = srv.Event("NewsItem", ts=t0 + 2, key="SPY", data={"sentiment": 0.9, "headline": "C"})

    for e in [e1, e2, e3]:
        cep.ingest(e)

    assert any(e.type == "NewsBurst" for e in emitted)

