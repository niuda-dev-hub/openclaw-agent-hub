from __future__ import annotations

from typing import Any, Dict, List, Optional

from .db import get_conn
from .utils import now_ms, new_id, dumps, loads
from .migrations import migrate


# NOTE: v0.1 repo is raw sqlite for speed. Later we can swap to SQLAlchemy.


def _ensure_schema(db_path=None) -> None:
    # TestClient may not trigger startup hooks consistently across environments.
    # Ensure schema exists for each operation (cheap after schema_version is set).
    migrate(db_path=db_path)


def create_agent(data: Dict[str, Any], db_path=None) -> Dict[str, Any]:
    _ensure_schema(db_path)
    agent_id = new_id()
    ts = now_ms()
    with get_conn(db_path) as conn:
        conn.execute(
            "INSERT INTO agents(id,name,description,agent_type,config_json,is_enabled,created_at) VALUES(?,?,?,?,?,?,?)",
            (
                agent_id,
                data["name"],
                data.get("description"),
                data.get("agent_type", "openclaw"),
                dumps(data.get("config", {})),
                1,
                ts,
            ),
        )
    return {
        "id": agent_id,
        "name": data["name"],
        "description": data.get("description"),
        "agent_type": data.get("agent_type", "openclaw"),
        "config": data.get("config", {}),
        "is_enabled": True,
        "created_at": ts,
    }


def list_agents(db_path=None) -> List[Dict[str, Any]]:
    _ensure_schema(db_path)
    with get_conn(db_path) as conn:
        rows = conn.execute("SELECT * FROM agents ORDER BY created_at DESC").fetchall()
    out = []
    for r in rows:
        out.append(
            {
                "id": r["id"],
                "name": r["name"],
                "description": r["description"],
                "agent_type": r["agent_type"],
                "config": loads(r["config_json"], {}),
                "is_enabled": bool(r["is_enabled"]),
                "created_at": r["created_at"],
                "last_heartbeat_at": r["last_heartbeat_at"] if "last_heartbeat_at" in r.keys() else None,
            }
        )
    return out


def get_agent(agent_id: str, db_path=None) -> Optional[Dict[str, Any]]:
    _ensure_schema(db_path)
    with get_conn(db_path) as conn:
        r = conn.execute("SELECT * FROM agents WHERE id=?", (agent_id,)).fetchone()
    if not r:
        return None
    return {
        "id": r["id"],
        "name": r["name"],
        "description": r["description"],
        "agent_type": r["agent_type"],
        "config": loads(r["config_json"], {}),
        "is_enabled": bool(r["is_enabled"]),
        "created_at": r["created_at"],
        "last_heartbeat_at": r["last_heartbeat_at"] if "last_heartbeat_at" in r.keys() else None,
    }


def update_agent(agent_id: str, patch: Dict[str, Any], db_path=None) -> Optional[Dict[str, Any]]:
    _ensure_schema(db_path)
    cur = get_agent(agent_id, db_path=db_path)
    if not cur:
        return None
    new_desc = patch.get("description", cur.get("description"))
    new_cfg = patch.get("config", cur.get("config", {}))
    new_enabled = patch.get("is_enabled", cur.get("is_enabled", True))
    with get_conn(db_path) as conn:
        conn.execute(
            "UPDATE agents SET description=?, config_json=?, is_enabled=? WHERE id=?",
            (new_desc, dumps(new_cfg), 1 if new_enabled else 0, agent_id),
        )
    return get_agent(agent_id, db_path=db_path)


def create_task(data: Dict[str, Any], db_path=None) -> Dict[str, Any]:
    _ensure_schema(db_path)
    task_id = new_id()
    ts = now_ms()
    with get_conn(db_path) as conn:
        conn.execute(
            "INSERT INTO tasks(id,title,prompt,input_json,constraints_json,expected_output_type,status,created_by,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
            (
                task_id,
                data["title"],
                data["prompt"],
                dumps(data.get("input", {})),
                dumps(data.get("constraints", {})),
                data.get("expected_output_type", "text"),
                data.get("status", "draft"),
                data.get("created_by"),
                ts,
                ts,
            ),
        )
    return get_task(task_id, db_path=db_path)  # type: ignore


def get_task(task_id: str, db_path=None) -> Optional[Dict[str, Any]]:
    _ensure_schema(db_path)
    with get_conn(db_path) as conn:
        r = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    if not r:
        return None
    return {
        "id": r["id"],
        "title": r["title"],
        "prompt": r["prompt"],
        "input": loads(r["input_json"], {}),
        "constraints": loads(r["constraints_json"], {}),
        "expected_output_type": r["expected_output_type"],
        "status": r["status"],
        "created_by": r["created_by"],
        "created_at": r["created_at"],
        "updated_at": r["updated_at"],
    }


def list_tasks(status: Optional[str] = None, db_path=None) -> List[Dict[str, Any]]:
    _ensure_schema(db_path)
    with get_conn(db_path) as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM tasks WHERE status=? ORDER BY created_at DESC", (status,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM tasks ORDER BY created_at DESC").fetchall()
    return [get_task(r["id"], db_path=db_path) for r in rows if r]  # type: ignore


def update_task(task_id: str, patch: Dict[str, Any], db_path=None) -> Optional[Dict[str, Any]]:
    _ensure_schema(db_path)
    cur = get_task(task_id, db_path=db_path)
    if not cur:
        return None
    ts = now_ms()
    merged = {
        "title": patch.get("title", cur["title"]),
        "prompt": patch.get("prompt", cur["prompt"]),
        "input": patch.get("input", cur["input"]),
        "constraints": patch.get("constraints", cur["constraints"]),
        "expected_output_type": patch.get(
            "expected_output_type", cur["expected_output_type"]
        ),
        "status": patch.get("status", cur["status"]),
    }
    with get_conn(db_path) as conn:
        conn.execute(
            "UPDATE tasks SET title=?, prompt=?, input_json=?, constraints_json=?, expected_output_type=?, status=?, updated_at=? WHERE id=?",
            (
                merged["title"],
                merged["prompt"],
                dumps(merged["input"]),
                dumps(merged["constraints"]),
                merged["expected_output_type"],
                merged["status"],
                ts,
                task_id,
            ),
        )
    return get_task(task_id, db_path=db_path)


def create_runs(task_id: str, agent_ids: List[str], run_params: Dict[str, Any], db_path=None) -> List[Dict[str, Any]]:
    _ensure_schema(db_path)
    ts = now_ms()
    run_ids: List[str] = []
    with get_conn(db_path) as conn:
        for aid in agent_ids:
            run_id = new_id()
            conn.execute(
                "INSERT INTO runs(id,task_id,agent_id,status,queued_at,run_params_json) VALUES(?,?,?,?,?,?)",
                (run_id, task_id, aid, "queued", ts, dumps(run_params)),
            )
            run_ids.append(run_id)

    # Read back using fresh connections (guaranteed committed)
    out = [get_run(rid, db_path=db_path) for rid in run_ids]
    return [r for r in out if r]


def fetch_queued_runs(limit: int = 10, db_path=None) -> List[Dict[str, Any]]:
    """Fetch queued runs in FIFO order."""

    _ensure_schema(db_path)
    with get_conn(db_path) as conn:
        rows = conn.execute(
            "SELECT id FROM runs WHERE status='queued' ORDER BY queued_at ASC LIMIT ?",
            (int(limit),),
        ).fetchall()
    out: List[Dict[str, Any]] = []
    for r in rows:
        run = get_run(r[0], db_path=db_path)
        if run:
            out.append(run)
    return out


def mark_run_running(run_id: str, db_path=None) -> Optional[Dict[str, Any]]:
    """Atomically transition queued->running."""

    _ensure_schema(db_path)
    ts = now_ms()
    with get_conn(db_path) as conn:
        cur = conn.execute(
            "UPDATE runs SET status='running', started_at=?, error_message=NULL "
            "WHERE id=? AND status='queued'",
            (ts, run_id),
        )
        if cur.rowcount == 0:
            return None
    return get_run(run_id, db_path=db_path)


def mark_run_finished(run_id: str, usage: Dict[str, Any] | None = None, db_path=None) -> Optional[Dict[str, Any]]:
    _ensure_schema(db_path)
    ts = now_ms()
    with get_conn(db_path) as conn:
        conn.execute(
            "UPDATE runs SET status='finished', finished_at=?, usage_json=? WHERE id=?",
            (ts, dumps(usage or {}), run_id),
        )
    return get_run(run_id, db_path=db_path)


def mark_run_failed(run_id: str, error_message: str, db_path=None) -> Optional[Dict[str, Any]]:
    _ensure_schema(db_path)
    ts = now_ms()
    with get_conn(db_path) as conn:
        conn.execute(
            "UPDATE runs SET status='failed', finished_at=?, error_message=? WHERE id=?",
            (ts, error_message, run_id),
        )
    return get_run(run_id, db_path=db_path)


def get_active_run_for_agent(task_id: str, agent_id: str, db_path=None) -> Optional[Dict[str, Any]]:
    """Return an active run for (task,agent) if any (queued/running)."""

    _ensure_schema(db_path)
    with get_conn(db_path) as conn:
        row = conn.execute(
            "SELECT id FROM runs WHERE task_id=? AND agent_id=? AND status IN ('queued','running') "
            "ORDER BY queued_at DESC LIMIT 1",
            (task_id, agent_id),
        ).fetchone()
    if not row:
        return None
    return get_run(row[0], db_path=db_path)


def list_participants(task_id: str, db_path=None) -> List[Dict[str, Any]]:
    """List participants for a task, aggregated by agent."""

    _ensure_schema(db_path)
    with get_conn(db_path) as conn:
        rows = conn.execute(
            "SELECT agent_id, COUNT(*) AS runs_count, MAX(queued_at) AS last_queued_at "
            "FROM runs WHERE task_id=? GROUP BY agent_id ORDER BY last_queued_at DESC",
            (task_id,),
        ).fetchall()

    out: List[Dict[str, Any]] = []
    for r in rows:
        aid = r["agent_id"]
        # Find latest run status for this agent
        with get_conn(db_path) as conn:
            last = conn.execute(
                "SELECT status FROM runs WHERE task_id=? AND agent_id=? ORDER BY queued_at DESC LIMIT 1",
                (task_id, aid),
            ).fetchone()
        a = get_agent(aid, db_path=db_path)
        out.append(
            {
                "agent_id": aid,
                "agent_name": a["name"] if a else None,
                "latest_status": last["status"] if last else None,
                "runs_count": int(r["runs_count"]),
            }
        )
    return out


def list_runs(task_id: str, db_path=None) -> List[Dict[str, Any]]:
    _ensure_schema(db_path)
    with get_conn(db_path) as conn:
        rows = conn.execute("SELECT id FROM runs WHERE task_id=? ORDER BY queued_at ASC", (task_id,)).fetchall()
    return [get_run(r[0], db_path=db_path) for r in rows if r]


def get_run(run_id: str, db_path=None) -> Optional[Dict[str, Any]]:
    # NOTE: do NOT call _ensure_schema() here; it would create nested connections
    # that may not see uncommitted rows from an outer transaction.
    with get_conn(db_path) as conn:
        r = conn.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
    if not r:
        return None
    return {
        "id": r["id"],
        "task_id": r["task_id"],
        "agent_id": r["agent_id"],
        "status": r["status"],
        "queued_at": r["queued_at"],
        "started_at": r["started_at"],
        "finished_at": r["finished_at"],
        "run_params": loads(r["run_params_json"], {}),
        "usage": loads(r["usage_json"], {}),
        "error_message": r["error_message"],
    }


def create_submission(run_id: str, data: Dict[str, Any], db_path=None) -> Dict[str, Any]:
    _ensure_schema(db_path)
    sub_id = new_id()
    ts = now_ms()
    run = get_run(run_id, db_path=db_path)
    if not run:
        raise KeyError("run_not_found")
    with get_conn(db_path) as conn:
        conn.execute(
            "INSERT INTO submissions(id,run_id,task_id,content_type,content,attachments_json,summary,created_at) VALUES(?,?,?,?,?,?,?,?)",
            (
                sub_id,
                run_id,
                run["task_id"],
                data.get("content_type", "text"),
                data["content"],
                dumps(data.get("attachments", [])),
                data.get("summary"),
                ts,
            ),
        )
    return get_submission(sub_id, db_path=db_path)  # type: ignore


def get_submission(submission_id: str, db_path=None) -> Optional[Dict[str, Any]]:
    _ensure_schema(db_path)
    with get_conn(db_path) as conn:
        r = conn.execute("SELECT * FROM submissions WHERE id=?", (submission_id,)).fetchone()
    if not r:
        return None
    return {
        "id": r["id"],
        "run_id": r["run_id"],
        "task_id": r["task_id"],
        "content_type": r["content_type"],
        "content": r["content"],
        "attachments": loads(r["attachments_json"], []),
        "summary": r["summary"],
        "created_at": r["created_at"],
    }


def list_submissions(task_id: str, db_path=None) -> List[Dict[str, Any]]:
    _ensure_schema(db_path)
    with get_conn(db_path) as conn:
        rows = conn.execute("SELECT id FROM submissions WHERE task_id=? ORDER BY created_at DESC", (task_id,)).fetchall()
    return [get_submission(r[0], db_path=db_path) for r in rows if r]


def create_evaluation(task_id: str, data: Dict[str, Any], db_path=None) -> Dict[str, Any]:
    _ensure_schema(db_path)
    ev_id = new_id()
    ts = now_ms()
    with get_conn(db_path) as conn:
        conn.execute(
            "INSERT INTO evaluations(id,task_id,submission_id,reviewer_id,source,rubric_json,total_score,comments,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
            (
                ev_id,
                task_id,
                data["submission_id"],
                data.get("reviewer_id"),
                data.get("source", "human"),
                dumps(data.get("rubric", {})),
                float(data["total_score"]),
                data.get("comments"),
                ts,
            ),
        )
    return get_evaluation(ev_id, db_path=db_path)  # type: ignore


def get_evaluation(ev_id: str, db_path=None) -> Optional[Dict[str, Any]]:
    _ensure_schema(db_path)
    with get_conn(db_path) as conn:
        r = conn.execute("SELECT * FROM evaluations WHERE id=?", (ev_id,)).fetchone()
    if not r:
        return None
    return {
        "id": r["id"],
        "task_id": r["task_id"],
        "submission_id": r["submission_id"],
        "reviewer_id": r["reviewer_id"],
        "source": r["source"],
        "rubric": loads(r["rubric_json"], {}),
        "total_score": float(r["total_score"]),
        "comments": r["comments"],
        "created_at": r["created_at"],
    }


def list_evaluations(task_id: str, db_path=None) -> List[Dict[str, Any]]:
    _ensure_schema(db_path)
    with get_conn(db_path) as conn:
        rows = conn.execute("SELECT id FROM evaluations WHERE task_id=? ORDER BY created_at DESC", (task_id,)).fetchall()
    return [get_evaluation(r[0], db_path=db_path) for r in rows if r]


def leaderboard(task_id: str, db_path=None) -> List[Dict[str, Any]]:
    _ensure_schema(db_path)
    # MVP: avg + count per submission
    with get_conn(db_path) as conn:
        rows = conn.execute(
            "SELECT submission_id, AVG(total_score) AS avg_score, COUNT(*) AS c "
            "FROM evaluations WHERE task_id=? GROUP BY submission_id ORDER BY avg_score DESC",
            (task_id,),
        ).fetchall()
    return [
        {
            "submission_id": r["submission_id"],
            "avg_score": float(r["avg_score"]),
            "review_count": int(r["c"]),
        }
        for r in rows
    ]


def set_decision(task_id: str, data: Dict[str, Any], db_path=None) -> Dict[str, Any]:
    _ensure_schema(db_path)
    dec_id = new_id()
    ts = now_ms()
    with get_conn(db_path) as conn:
        conn.execute(
            "INSERT INTO decisions(id,task_id,winner_submission_id,decided_by,rationale,created_at) VALUES(?,?,?,?,?,?)",
            (
                dec_id,
                task_id,
                data["winner_submission_id"],
                data.get("decided_by"),
                data.get("rationale"),
                ts,
            ),
        )
    return get_decision(task_id, db_path=db_path)  # type: ignore


def get_decision(task_id: str, db_path=None) -> Optional[Dict[str, Any]]:
    _ensure_schema(db_path)
    with get_conn(db_path) as conn:
        r = conn.execute("SELECT * FROM decisions WHERE task_id=?", (task_id,)).fetchone()
    if not r:
        return None
    return {
        "id": r["id"],
        "task_id": r["task_id"],
        "winner_submission_id": r["winner_submission_id"],
        "decided_by": r["decided_by"],
        "rationale": r["rationale"],
        "created_at": r["created_at"],
    }


def add_event(task_id: str | None, event_type: str, actor_type: str = "system", actor_id: str | None = None, payload: Dict[str, Any] | None = None, db_path=None) -> None:
    _ensure_schema(db_path)
    ev_id = new_id()
    ts = now_ms()
    with get_conn(db_path) as conn:
        conn.execute(
            "INSERT INTO events(id,task_id,event_type,actor_type,actor_id,payload_json,created_at) VALUES(?,?,?,?,?,?,?)",
            (ev_id, task_id, event_type, actor_type, actor_id, dumps(payload or {}), ts),
        )


def list_events(task_id: str, limit: int = 50, db_path=None) -> List[Dict[str, Any]]:
    """查询指定任务的审计事件列表（按时间倒序）。"""
    _ensure_schema(db_path)
    with get_conn(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM events WHERE task_id=? ORDER BY created_at DESC LIMIT ?",
            (task_id, int(limit)),
        ).fetchall()
    return [
        {
            "id": r["id"],
            "task_id": r["task_id"],
            "event_type": r["event_type"],
            "actor_type": r["actor_type"],
            "actor_id": r["actor_id"],
            "payload": loads(r["payload_json"], {}),
            "created_at": r["created_at"],
        }
        for r in rows
    ]


def update_agent_heartbeat(agent_id: str, db_path=None) -> Optional[Dict[str, Any]]:
    """更新 Agent 心跳时间戳，用于在线状态判断。"""
    _ensure_schema(db_path)
    ts = now_ms()
    with get_conn(db_path) as conn:
        cur = conn.execute(
            "UPDATE agents SET last_heartbeat_at=? WHERE id=?",
            (ts, agent_id),
        )
        if cur.rowcount == 0:
            return None
    return get_agent(agent_id, db_path=db_path)
