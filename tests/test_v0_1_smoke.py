from fastapi.testclient import TestClient

from agent_hub.main import app


def test_v0_1_smoke_flow():
    c = TestClient(app)

    # create agents
    a1 = c.post(
        "/api/v0.1/agents",
        json={"name": "agent-A", "agent_type": "mock", "config": {"x": 1}},
    ).json()
    a2 = c.post(
        "/api/v0.1/agents",
        json={"name": "agent-B", "agent_type": "mock", "config": {"x": 2}},
    ).json()

    # create task
    t = c.post(
        "/api/v0.1/tasks",
        json={
            "title": "T1",
            "prompt": "do something",
            "input": {"k": "v"},
            "constraints": {"lang": "zh"},
            "expected_output_type": "text",
        },
    ).json()

    # start task with two agents
    runs = c.post(
        f"/api/v0.1/tasks/{t['id']}/start",
        json={"agent_ids": [a1["id"], a2["id"]], "run_params": {"temp": 0.2}},
    ).json()
    assert len(runs) == 2

    # submit
    sids = []
    for r in runs:
        sub = c.post(
            f"/api/v0.1/runs/{r['id']}/submit",
            json={"content_type": "text", "content": f"result for {r['agent_id']}"},
        ).json()
        sids.append(sub["id"])

    # evaluate
    for i, sid in enumerate(sids):
        ev = c.post(
            f"/api/v0.1/tasks/{t['id']}/evaluations",
            json={
                "submission_id": sid,
                "source": "human",
                "rubric": {"correctness": 30 + i},
                "reward_usd": 80 + i,
            },
        )
        assert ev.status_code == 200

    # leaderboard
    lb = c.get(f"/api/v0.1/tasks/{t['id']}/leaderboard").json()
    assert len(lb) == 2
    assert lb[0]["avg_reward_usd"] >= lb[1]["avg_reward_usd"]

    # decision
    winner = lb[0]["submission_id"]
    d = c.post(
        f"/api/v0.1/tasks/{t['id']}/decision",
        json={"winner_submission_id": winner, "rationale": "best"},
    )
    assert d.status_code == 200

    # decision exists
    d2 = c.get(f"/api/v0.1/tasks/{t['id']}/decision")
    assert d2.status_code == 200
