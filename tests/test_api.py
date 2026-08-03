from fastapi.testclient import TestClient

from chanlun_visual.api import app
from chanlun_visual.providers import canonical_symbol


client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0", "execution_allowed": False}


def test_demo_and_html_export():
    demo = client.get("/api/demo").json()
    analysis = demo["frames"]["1d"]
    response = client.post("/api/export/html", json={"analysis": analysis})
    assert response.status_code == 200
    assert "NO_ACTION" in response.text
    assert "execution_allowed=false" in response.text
    assert "<svg" in response.text


def test_bad_input_is_422():
    response = client.post(
        "/api/analyze",
        json={
            "symbol": "X",
            "timeframe": "1d",
            "bars": [{"date": "2026-01-01", "open": 2, "high": 1, "low": 0.5, "close": 2}],
        },
    )
    assert response.status_code == 422


def test_common_market_symbols_are_canonicalized():
    assert canonical_symbol("300684") == "300684.SZ"
    assert canonical_symbol("600519") == "600519.SS"
    assert canonical_symbol("0700") == "0700.HK"
    assert canonical_symbol("AAPL") == "AAPL"
