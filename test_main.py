from fastapi.testclient import TestClient
from app.main import app
from app.dependencies import history, HISTORY_MAX

import pytest

client = TestClient(app)

# POST
def test_basic_division():
    r = client.post("/calculate", json={"expr": "30/4"})
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert abs(data["result"] - 7.5) < 1e-9
 
def test_percent_subtraction():
    r = client.post("/calculate", json={"expr": "100 - 6%"})
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert abs(data["result"] - 94.0) < 1e-9
 
def test_standalone_percent():
    r = client.post("/calculate", json={"expr": "6%"})
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert abs(data["result"] - 0.06) < 1e-9
 
def test_invalid_expr_returns_ok_false():
    r = client.post("/calculate", json={"expr": "2**(3"})
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is False
    assert "error" in data and data["error"] != ""
 
def test_calculate_missing_expr_field_returns_422():
    # Expression requires `expr`, posting without it should fail.
    r = client.post("/calculate", json={})
    assert r.status_code == 422
 
def test_calculate_rejects_query_param_style_request():
    # /calculate expects an expression object in the JSON body.
    r = client.post("/calculate", params={"expr": "1+1"})
    assert r.status_code == 422

# GET
def test_get_history_empty():
    r = client.get("/history")
    assert r.status_code == 200
    assert r.json() == []
 
def test_get_history_returns_recent_first():
    client.post("/calculate", json={"expr": "1+1"})
    client.post("/calculate", json={"expr": "2+2"})
    client.post("/calculate", json={"expr": "3+3"})
 
    r = client.get("/history")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 3
    # recent calculation should be first
    assert data[0]["expr"] == "3+3"
    assert data[0]["result"] == 6
    assert data[-1]["expr"] == "1+1"
 
def test_get_history_respects_limit():
    for expr in ["1+1", "2+2", "3+3", "4+4", "5+5"]:
        client.post("/calculate", json={"expr": expr})
 
    r = client.get("/history", params={"limit": 2})
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2
    # should return the 2 most recent
    assert data[0]["expr"] == "5+5"
    assert data[1]["expr"] == "4+4"
 
def test_get_history_matches_calculatorlog_shape():
    client.post("/calculate", json={"expr": "8*8"})
 
    r = client.get("/history")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    entry = data[0]
    assert set(entry.keys()) == {"timestamp", "expr", "result"}
    assert isinstance(entry["timestamp"], str)
    assert isinstance(entry["expr"], str)
    assert isinstance(entry["result"], float)
 
def test_get_history_limit_out_of_range_is_rejected():
    r = client.get("/history", params={"limit": 0})
    assert r.status_code == 422
 
    r = client.get("/history", params={"limit": HISTORY_MAX + 1})
    assert r.status_code == 422

# DELETE
@pytest.fixture(autouse=True)
def clear_history():
    history.clear()
    yield
    history.clear()

def test_delete_history_clears_entries():
    client.post("/calculate", json={"expr": "10*10"})
    client.post("/calculate", json={"expr": "20*20"})
 
    r = client.delete("/history")
    assert r.status_code == 200
    assert r.json() == {"ok": True, "cleared": True}
 
    r = client.get("/history")
    assert r.json() == []
 
def test_delete_history_on_empty_history_still_succeeds():
    r = client.delete("/history")
    assert r.status_code == 200
    assert r.json() == {"ok": True, "cleared": True}
 
def test_delete_history_does_not_affect_future_calculations():
    client.post("/calculate", json={"expr": "5+5"})
    client.delete("/history")
 
    r = client.post("/calculate", json={"expr": "7+7"})
    assert r.status_code == 200
    assert r.json()["ok"] is True
 
    r = client.get("/history")
    data = r.json()
    assert len(data) == 1
    assert data[0]["expr"] == "7+7"