from agent_hub import repo


def test_claim_participation_schema_migrates(tmp_path):
    db_path = tmp_path / "hub.db"

    # should not raise
    repo._ensure_schema(db_path=str(db_path))


def test_claim_participation_minimal_roundtrip(tmp_path):
    db_path = tmp_path / "hub.db"

    # for now we only assert the existing primitives stay usable;
    # claim/participation will be wired in a follow-up once schema is finalized.
    agent = repo.create_agent({"name": "worker-a", "description": "", "agent_type": "openclaw", "config": {"runtime": "dummy"}}, db_path=str(db_path))
    task = repo.create_task({
        "title": "demo",
        "prompt": "do something",
        "input": {},
        "constraints": {},
        "expected_output_type": "text",
        "created_by": "test",
    }, db_path=str(db_path))

    runs = repo.create_runs(task["id"], [agent["id"]], {"mode": "test"}, db_path=str(db_path))
    assert runs
    run = runs[0]

    sub = repo.create_submission(run["id"], {
        "content_type": "text",
        "content": "ok",
        "attachments": [],
        "summary": "demo",
    }, db_path=str(db_path))

    assert sub["task_id"] == task["id"]
    assert sub["run_id"] == run["id"]

    ev = repo.create_evaluation(task["id"], {
        "submission_id": sub["id"],
        "reviewer_id": "tester",
        "source": "human",
        "rubric": {"q": 5},
        "reward_usd": 5.0,
        "comments": "looks good",
    }, db_path=str(db_path))

    assert ev["task_id"] == task["id"]
    assert ev["submission_id"] == sub["id"]

    lb = repo.leaderboard(task["id"], db_path=str(db_path))
    assert lb
    assert lb[0]["submission_id"] == sub["id"]
