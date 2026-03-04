from __future__ import annotations

from fastapi import FastAPI, HTTPException

from .migrations import migrate
from . import repo
from .schemas import (
    AgentCreate,
    AgentRead,
    AgentUpdate,
    TaskCreate,
    TaskRead,
    TaskUpdate,
    TaskStart,
    TaskClaim,
    ParticipantEntry,
    RunRead,
    SubmissionCreate,
    SubmissionRead,
    EvaluationCreate,
    EvaluationRead,
    LeaderboardEntry,
    DecisionCreate,
    DecisionRead,
    EventRead,
)

app = FastAPI(title="OpenClaw Agent Hub", version="0.1.0")


@app.on_event("startup")
def _startup() -> None:
    migrate()


@app.get("/health")
def health():
    return {"status": "ok", "service": "openclaw-agent-hub"}


# Agents
@app.get("/api/v0.1/agents", response_model=list[AgentRead])
def api_list_agents():
    return repo.list_agents()


@app.post("/api/v0.1/agents", response_model=AgentRead)
def api_create_agent(body: AgentCreate):
    try:
        a = repo.create_agent(body.model_dump())
        repo.add_event(None, "agent_created", payload={"agent_id": a["id"], "name": a["name"]})
        return a
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v0.1/agents/{agent_id}", response_model=AgentRead)
def api_get_agent(agent_id: str):
    a = repo.get_agent(agent_id)
    if not a:
        raise HTTPException(status_code=404, detail="agent_not_found")
    return a


@app.patch("/api/v0.1/agents/{agent_id}", response_model=AgentRead)
def api_patch_agent(agent_id: str, body: AgentUpdate):
    a = repo.update_agent(agent_id, body.model_dump(exclude_unset=True))
    if not a:
        raise HTTPException(status_code=404, detail="agent_not_found")
    repo.add_event(None, "agent_updated", payload={"agent_id": agent_id})
    return a


@app.post("/api/v0.1/agents/{agent_id}/heartbeat", response_model=AgentRead)
def api_agent_heartbeat(agent_id: str):
    """Agent 心跳接口：Agent 定期调用此接口以表明自己在线。"""
    a = repo.update_agent_heartbeat(agent_id)
    if not a:
        raise HTTPException(status_code=404, detail="agent_not_found")
    return a


# Tasks
@app.post("/api/v0.1/tasks", response_model=TaskRead)
def api_create_task(body: TaskCreate):
    t = repo.create_task(body.model_dump())
    repo.add_event(t["id"], "task_created", payload={"task_id": t["id"], "title": t["title"]})
    return t


@app.get("/api/v0.1/tasks", response_model=list[TaskRead])
def api_list_tasks(status: str | None = None):
    return repo.list_tasks(status=status)


@app.get("/api/v0.1/tasks/{task_id}", response_model=TaskRead)
def api_get_task(task_id: str):
    t = repo.get_task(task_id)
    if not t:
        raise HTTPException(status_code=404, detail="task_not_found")
    return t


@app.patch("/api/v0.1/tasks/{task_id}", response_model=TaskRead)
def api_patch_task(task_id: str, body: TaskUpdate):
    t = repo.update_task(task_id, body.model_dump(exclude_unset=True))
    if not t:
        raise HTTPException(status_code=404, detail="task_not_found")
    repo.add_event(task_id, "task_updated", payload={"task_id": task_id})
    return t


@app.post("/api/v0.1/tasks/{task_id}/start", response_model=list[RunRead])
def api_start_task(task_id: str, body: TaskStart):
    t = repo.get_task(task_id)
    if not t:
        raise HTTPException(status_code=404, detail="task_not_found")
    # Move to running
    repo.update_task(task_id, {"status": "running"})
    runs = repo.create_runs(task_id, body.agent_ids, body.run_params)
    repo.add_event(task_id, "task_started", payload={"task_id": task_id, "agent_ids": body.agent_ids})
    return runs


@app.post("/api/v0.1/tasks/{task_id}/claim", response_model=RunRead)
def api_claim_task(task_id: str, body: TaskClaim):
    t = repo.get_task(task_id)
    if not t:
        raise HTTPException(status_code=404, detail="task_not_found")
    a = repo.get_agent(body.agent_id)
    if not a:
        raise HTTPException(status_code=404, detail="agent_not_found")

    active = repo.get_active_run_for_agent(task_id, body.agent_id)
    if active:
        # idempotent: claiming again returns current active run
        return active

    # Ensure task is running/open once someone participates
    if t.get("status") in ("draft", "open"):
        repo.update_task(task_id, {"status": "running"})

    run = repo.create_runs(task_id, [body.agent_id], body.run_params)[0]
    repo.add_event(
        task_id,
        "claimed",
        actor_type="agent",
        actor_id=body.agent_id,
        payload={"task_id": task_id, "run_id": run["id"]},
    )
    return run


@app.get("/api/v0.1/tasks/{task_id}/participants", response_model=list[ParticipantEntry])
def api_list_participants(task_id: str):
    t = repo.get_task(task_id)
    if not t:
        raise HTTPException(status_code=404, detail="task_not_found")
    return repo.list_participants(task_id)


@app.get("/api/v0.1/tasks/{task_id}/runs", response_model=list[RunRead])
def api_list_runs(task_id: str):
    """\u67e5询任务的所有 Run。"""
    return repo.list_runs(task_id)


@app.get("/api/v0.1/runs/{run_id}", response_model=RunRead)
def api_get_run(run_id: str):
    r = repo.get_run(run_id)
    if not r:
        raise HTTPException(status_code=404, detail="run_not_found")
    return r


# Submissions
@app.post("/api/v0.1/runs/{run_id}/submit", response_model=SubmissionRead)
def api_submit(run_id: str, body: SubmissionCreate):
    try:
        s = repo.create_submission(run_id, body.model_dump())
        repo.add_event(s["task_id"], "submitted", actor_type="agent", actor_id=None, payload={"run_id": run_id, "submission_id": s["id"]})
        return s
    except KeyError:
        raise HTTPException(status_code=404, detail="run_not_found")


@app.get("/api/v0.1/tasks/{task_id}/submissions", response_model=list[SubmissionRead])
def api_list_submissions(task_id: str):
    return repo.list_submissions(task_id)


@app.get("/api/v0.1/submissions/{submission_id}", response_model=SubmissionRead)
def api_get_submission(submission_id: str):
    s = repo.get_submission(submission_id)
    if not s:
        raise HTTPException(status_code=404, detail="submission_not_found")
    return s


# Evaluations
@app.post("/api/v0.1/tasks/{task_id}/evaluations", response_model=EvaluationRead)
def api_create_evaluation(task_id: str, body: EvaluationCreate):
    t = repo.get_task(task_id)
    if not t:
        raise HTTPException(status_code=404, detail="task_not_found")
    ev = repo.create_evaluation(task_id, body.model_dump())
    repo.add_event(task_id, "evaluated", actor_type="user" if body.source == "human" else "system", actor_id=body.reviewer_id, payload={"submission_id": body.submission_id, "total_score": body.total_score})
    return ev


@app.get("/api/v0.1/tasks/{task_id}/evaluations", response_model=list[EvaluationRead])
def api_list_evaluations(task_id: str):
    return repo.list_evaluations(task_id)


@app.get("/api/v0.1/tasks/{task_id}/leaderboard", response_model=list[LeaderboardEntry])
def api_leaderboard(task_id: str):
    return repo.leaderboard(task_id)


# Decision
@app.post("/api/v0.1/tasks/{task_id}/decision", response_model=DecisionRead)
def api_set_decision(task_id: str, body: DecisionCreate):
    t = repo.get_task(task_id)
    if not t:
        raise HTTPException(status_code=404, detail="task_not_found")
    if repo.get_decision(task_id):
        raise HTTPException(status_code=400, detail="decision_already_set")
    d = repo.set_decision(task_id, body.model_dump())
    repo.update_task(task_id, {"status": "finalized"})
    repo.add_event(task_id, "decided", actor_type="user", actor_id=body.decided_by, payload={"winner_submission_id": body.winner_submission_id})
    return d


@app.get("/api/v0.1/tasks/{task_id}/decision", response_model=DecisionRead)
def api_get_decision(task_id: str):
    d = repo.get_decision(task_id)
    if not d:
        raise HTTPException(status_code=404, detail="decision_not_found")
    return d


@app.get("/api/v0.1/tasks/{task_id}/events", response_model=list[EventRead])
def api_list_events(task_id: str, limit: int = 50):
    """\u7b2c\u4e00\u4e2a\u5ba1\u8ba1\u4e8b\u4ef6\u6d41\u63a5\u53e3\uff08v0.1 \u89c4\u683c\u4e2d\u5b9a\u4e49\u4f46\u672a\u5b9e\u73b0\uff09\u3002"""
    t = repo.get_task(task_id)
    if not t:
        raise HTTPException(status_code=404, detail="task_not_found")
    return repo.list_events(task_id, limit=limit)
