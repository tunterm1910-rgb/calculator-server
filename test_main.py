from fastapi.testclient import TestClient
from main import app, history # or whatever your app module is

import pytest

client = TestClient(app)

def test_basic_division():
    r = client.post("/calculate", params={"expr": "30/4"})
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert abs(data["result"] - 7.5) < 1e-9

def test_percent_subtraction():
    r = client.post("/calculate", params={"expr": "100 - 6%"})
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert abs(data["result"] - 94.0) < 1e-9

def test_standalone_percent():
    r = client.post("/calculate", params={"expr": "6%"})
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert abs(data["result"] - 0.06) < 1e-9

def test_invalid_expr_returns_ok_false():
    r = client.post("/calculate", params={"expr": "2**(3"})
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is False
    assert "error" in data and data["error"] != ""


# TODO Add more tests

# GET
def test_get_history_empty():
    r = client.get("/history")
    assert r.status_code == 200
    assert r.json() == []
 
def test_get_history_returns_recent_first():
    client.post("/calculate", params={"expr": "1+1"})
    client.post("/calculate", params={"expr": "2+2"})
    client.post("/calculate", params={"expr": "3+3"})
 
    r = client.get("/history")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 3
    # most recent should be first
    assert data[0]["expr"] == "3+3"
    assert data[0]["result"] == 6
    assert data[-1]["expr"] == "1+1"
 
def test_get_history_respects_limit():
    for expr in ["1+1", "2+2", "3+3", "4+4", "5+5"]:
        client.post("/calculate", params={"expr": expr})
 
    r = client.get("/history", params={"limit": 2})
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2
    # should return the 2 most recent
    assert data[0]["expr"] == "5+5"
    assert data[1]["expr"] == "4+4"

# DELETE
@pytest.fixture(autouse=True)
def clear_history():
    history.clear()
    yield
    history.clear()

def test_delete_history_clears_entries():
    client.post("/calculate", params={"expr": "10*10"})
    client.post("/calculate", params={"expr": "20*20"})
 
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
    client.post("/calculate", params={"expr": "5+5"})
    client.delete("/history")
 
    r = client.post("/calculate", params={"expr": "7+7"})
    assert r.status_code == 200
    assert r.json()["ok"] is True
 
    r = client.get("/history")
    data = r.json()
    assert len(data) == 1
    assert data[0]["expr"] == "7+7"