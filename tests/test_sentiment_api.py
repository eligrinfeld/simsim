from fastapi.testclient import TestClient
from services.sentiment_api.app import app


def test_score_news_batch_basic():
    client = TestClient(app)
    payload = [
        {"id": "1", "title": "Stock surges on strong earnings"},
        {"id": "2", "title": "Shares plunge after weak outlook"},
        {"id": "3", "title": "Flat day"},
    ]
    resp = client.post("/score_news_batch", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list) and len(data) == 3
    assert set(data[0].keys()) == {"id", "sentiment_score"}
    assert isinstance(data[0]["sentiment_score"], float)
