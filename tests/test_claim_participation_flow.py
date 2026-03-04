from fastapi.testclient import TestClient

from agent_hub.main import app


def test_claim_is_idempotent_and_supports_multiple_agents():
    c = TestClient(app)

    a1 = c.post(
        "/api/v0.1/agents",
        json={"name": "agent-claim-A", "agent_type": "mock", "config": {"x": 1}},
    ).json()
    a2 = c.post(
        "/api/v0.1/agents",
        json={"name": "agent-claim-B", "agent_type": "mock", "config": {"x": 2}},
    ).json()

    t = c.post(
        "/api/v0.1/tasks",
        json={"title": "T-claim", "prompt": "do", "expected_output_type": "text"},
    ).json()

    # A claims twice -> same active run
    r1 = c.post(
        f"/api/v0.1/tasks/{t['id']}/claim",
        json={"agent_id": a1["id"], "run_params": {"temp": 0.2}},
    ).json()
    r1b = c.post(
        f"/api/v0.1/tasks/{t['id']}/claim",
        json={"agent_id": a1["id"], "run_params": {"temp": 0.9}},
    ).json()
    assert r1b["id"] == r1["id"]

    # Another agent can also claim
    r2 = c.post(
        f"/api/v0.1/tasks/{t['id']}/claim",
        json={"agent_id": a2["id"], "run_params": {"temp": 0.3}},
    ).json()
    assert r2["id"] != r1["id"]

    parts = c.get(f"/api/v0.1/tasks/{t['id']}/participants").json()
    assert len(parts) == 2
    assert {p["agent_id"] for p in parts} == {a1["id"], a2["id"]}
