from __future__ import annotations

from fastapi.testclient import TestClient

from app import app


client = TestClient(app)


def test_health_endpoint() -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


def test_tasks_endpoint() -> None:
    resp = client.get("/tasks")
    assert resp.status_code == 200
    data = resp.json()
    assert "tasks" in data
    assert len(data["tasks"]) >= 3


def test_reset_step_state_contract() -> None:
    reset_resp = client.post("/reset", json={"task_id": "easy", "seed": 123})
    assert reset_resp.status_code == 200
    obs = reset_resp.json()
    assert obs["task_id"] == "easy"
    assert len(obs["feed_items"]) > 0

    first_item_id = obs["feed_items"][0]["id"]
    step_resp = client.post(
        "/step",
        json={
            "task_id": "easy",
            "action": {
                "action_type": "recommend_item",
                "item_id": first_item_id,
                "rationale": "API contract test action",
            },
        },
    )
    assert step_resp.status_code == 200
    payload = step_resp.json()

    assert "observation" in payload
    assert "reward" in payload
    assert "done" in payload
    assert "info" in payload
    assert 0.0 <= payload["reward"]["value"] <= 1.0

    state_resp = client.get("/state", params={"task_id": "easy"})
    assert state_resp.status_code == 200
    state = state_resp.json()
    assert state["step"] >= 1
