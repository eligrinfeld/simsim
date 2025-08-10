import importlib.util
from fastapi.testclient import TestClient


def test_analyze_shape_basic():
    # Load the stock analyzer app
    spec = importlib.util.spec_from_file_location("stock_app", "apps/stock_analyzer/app.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)

    client = TestClient(mod.app)
    resp = client.get("/analyze", params={"ticker": "AAPL"})
    assert resp.status_code == 200
    data = resp.json()

    # Basic shape checks
    for key in [
        "symbol",
        "price",
        "scores",
        "traditional_scores",
        "macro_scores",
        "technicals",
        "fundamentals",
        "series",
        "sentiment_series",
        "percentiles",
        "percentiles_meta",
        "peers",
        "deltas",
    ]:
        assert key in data, f"missing key: {key}"

    assert isinstance(data["scores"], dict)
    assert isinstance(data["traditional_scores"], dict)
    assert isinstance(data["macro_scores"], dict)
    assert isinstance(data["percentiles_meta"], dict)

    # Ensure price and score fields are sane
    assert isinstance(data["price"], (int, float))
    assert 0 <= data["scores"].get("valuation", 0) <= 5
    assert 0 <= data["traditional_scores"].get("rsi_position", 0) <= 5

