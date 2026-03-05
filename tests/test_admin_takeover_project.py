from fastapi.testclient import TestClient

from agent_hub.main import app


def test_admin_takeover_refunds_stake_and_mints_bonus_idempotent():
    c = TestClient(app)

    agent = c.post(
        "/api/v0.1/agents",
        json={"name": "agent-idea", "agent_type": "mock", "config": {}},
    ).json()

    p = c.post(
        "/api/v0.1/projects",
        json={
            "title": "P-good",
            "description": "nice",
            "publisher_type": "agent",
            "publisher_id": agent["id"],
            "stake_points": 50,
        },
    ).json()

    body = {"bonus_reward": 30, "reason": "good idea", "idempotency_key": "k1", "admin_id": "admin"}

    r1 = c.post(f"/api/v0.1/admin/projects/{p['id']}/takeover", json=body).json()
    assert r1["project_id"] == p["id"]
    assert r1["stake_refund"] == 50
    assert r1["bonus_reward"] == 30

    # second call should not duplicate
    r2 = c.post(f"/api/v0.1/admin/projects/{p['id']}/takeover", json=body).json()
    assert r2["id"] == r1["id"]
    assert r2["stake_refund"] == 50
    assert r2["bonus_reward"] == 30

    # project publisher becomes admin and stake cleared
    p2 = c.get(f"/api/v0.1/projects/{p['id']}").json()
    assert p2["publisher_type"] == "admin"
    assert p2["publisher_id"] == "admin"
    assert p2["stake_points"] == 0
