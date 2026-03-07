from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..db import get_conn
from ..utils import now_ms, new_id, dumps, loads
from ..migrations import migrate


# ---- Points / Projects helpers (v0.1+) ----


def add_ledger_entry(
    actor_type: str,
    actor_id: str,
    delta: int,
    event_type: str,
    ref_type: str | None = None,
    ref_id: str | None = None,
    meta: Dict[str, Any] | None = None,
    *,
    conn=None,
    db_path=None,
    entry_id: str | None = None,
) -> Dict[str, Any]:
    """Append a points ledger entry.

    If conn is provided, uses that connection (for transactional writes).
    """

    _ensure_schema(db_path)
    lid = entry_id or new_id()
    ts = now_ms()
    sql = (
        "INSERT INTO points_ledger(id,actor_type,actor_id,delta,event_type,ref_type,ref_id,meta_json,created_at) "
        "VALUES(?,?,?,?,?,?,?,?,?)"
    )
    params = (lid, actor_type, actor_id, int(delta), event_type, ref_type, ref_id, dumps(meta or {}), ts)
    if conn is not None:
        conn.execute(sql, params)
    else:
        with get_conn(db_path) as c:
            c.execute(sql, params)
    return {
        "id": lid,
        "actor_type": actor_type,
        "actor_id": actor_id,
        "delta": int(delta),
        "event_type": event_type,
        "ref_type": ref_type,
        "ref_id": ref_id,
        "meta": meta or {},
        "created_at": ts,
    }


def get_points_balance(actor_type: str, actor_id: str, db_path=None) -> int:
    _ensure_schema(db_path)
    with get_conn(db_path) as conn:
        row = conn.execute(
            "SELECT COALESCE(SUM(delta),0) AS bal FROM points_ledger WHERE actor_type=? AND actor_id=?",
            (actor_type, actor_id),
        ).fetchone()
    return int(row[0] if row else 0)


def create_project(data: Dict[str, Any], db_path=None) -> Dict[str, Any]:
    _ensure_schema(db_path)
    pid = new_id()
    ts = now_ms()
    with get_conn(db_path) as conn:
        conn.execute(
            "INSERT INTO projects(id,title,description,publisher_type,publisher_id,stake_points,status,created_at,updated_at) "
            "VALUES(?,?,?,?,?,?,?,?,?)",
            (
                pid,
                data["title"],
                data.get("description"),
                data.get("publisher_type", "agent"),
                data["publisher_id"],
                int(data.get("stake_points", 0)),
                data.get("status", "active"),
                ts,
                ts,
            ),
        )
    return get_project(pid, db_path=db_path)  # type: ignore


def get_project(project_id: str, db_path=None) -> Optional[Dict[str, Any]]:
    _ensure_schema(db_path)
    with get_conn(db_path) as conn:
        r = conn.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
    if not r:
        return None
    return {
        "id": r["id"],
        "title": r["title"],
        "description": r["description"],
        "publisher_type": r["publisher_type"],
        "publisher_id": r["publisher_id"],
        "stake_points": int(r["stake_points"]),
        "status": r["status"],
        "created_at": r["created_at"],
        "updated_at": r["updated_at"],
    }


def admin_takeover_project(
    project_id: str,
    *,
    bonus_reward: int = 0,
    reason: str | None = None,
    admin_id: str = "admin",
    idempotency_key: str | None = None,
    db_path=None,
) -> Dict[str, Any]:
    """Admin takeover: publisher -> admin, refund ALL stake_points to original publisher,
    and optionally mint a bonus reward from system treasury.

    Rules per user:
    - bonus source: system treasury (mint)
    - stake: single stake_points on project
    - takeover allowed any time
    - admin is a single super admin

    Idempotency:
    - If idempotency_key provided: create ledger entry ids deterministically based on it.
    - Also, project_takeovers has UNIQUE(project_id) so second attempt returns existing record.
    """

    _ensure_schema(db_path)

    # Deterministic ids for idempotency (simple v0.1)
    # Using a stable prefix makes debugging easier.
    def _eid(suffix: str) -> str:
        if not idempotency_key:
            return new_id()
        return f"takeover:{project_id}:{idempotency_key}:{suffix}"

    with get_conn(db_path) as conn:
        # If already taken over, return record
        existing = conn.execute(
            "SELECT * FROM project_takeovers WHERE project_id=?",
            (project_id,),
        ).fetchone()
        if existing:
            return {
                "id": existing["id"],
                "project_id": existing["project_id"],
                "from_publisher_type": existing["from_publisher_type"],
                "from_publisher_id": existing["from_publisher_id"],
                "to_publisher_type": existing["to_publisher_type"],
                "to_publisher_id": existing["to_publisher_id"],
                "stake_refund": int(existing["stake_refund"]),
                "bonus_reward": int(existing["bonus_reward"]),
                "reason": existing["reason"],
                "admin_id": existing["admin_id"],
                "created_at": existing["created_at"],
            }

        proj = conn.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
        if not proj:
            raise KeyError("project_not_found")

        from_pt = proj["publisher_type"]
        from_pid = proj["publisher_id"]
        stake = int(proj["stake_points"])
        ts = now_ms()

        # 1) refund stake to original publisher (single stake)
        if stake > 0:
            add_ledger_entry(
                from_pt,
                from_pid,
                +stake,
                "PROJECT_STAKE_REFUND",
                ref_type="project",
                ref_id=project_id,
                meta={"reason": "admin_takeover_refund"},
                conn=conn,
                entry_id=_eid("stake_refund"),
            )

        # 2) bonus reward minted from system treasury
        b = int(bonus_reward or 0)
        if b < 0:
            raise ValueError("bonus_reward_must_be_non_negative")
        if b > 0:
            add_ledger_entry(
                "system",
                "treasury",
                -b,
                "TREASURY_MINT_OUT",
                ref_type="project",
                ref_id=project_id,
                meta={"to": f"{from_pt}:{from_pid}"},
                conn=conn,
                entry_id=_eid("treasury_out"),
            )
            add_ledger_entry(
                from_pt,
                from_pid,
                +b,
                "PROJECT_IDEA_BONUS",
                ref_type="project",
                ref_id=project_id,
                meta={"admin_id": admin_id, "reason": reason or ""},
                conn=conn,
                entry_id=_eid("bonus"),
            )

        # 3) update project publisher -> admin and clear stake
        conn.execute(
            "UPDATE projects SET publisher_type=?, publisher_id=?, stake_points=0, updated_at=? WHERE id=?",
            ("admin", admin_id, ts, project_id),
        )

        # 4) create takeover record
        takeover_id = _eid("record")
        conn.execute(
            "INSERT INTO project_takeovers(id,project_id,from_publisher_type,from_publisher_id,to_publisher_type,to_publisher_id,stake_refund,bonus_reward,reason,admin_id,created_at) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (
                takeover_id,
                project_id,
                from_pt,
                from_pid,
                "admin",
                admin_id,
                stake,
                b,
                reason,
                admin_id,
                ts,
            ),
        )

    # read with a fresh conn
    with get_conn(db_path) as conn2:
        r = conn2.execute("SELECT * FROM project_takeovers WHERE project_id=?", (project_id,)).fetchone()
    return {
        "id": r["id"],
        "project_id": r["project_id"],
        "from_publisher_type": r["from_publisher_type"],
        "from_publisher_id": r["from_publisher_id"],
        "to_publisher_type": r["to_publisher_type"],
        "to_publisher_id": r["to_publisher_id"],
        "stake_refund": int(r["stake_refund"]),
        "bonus_reward": int(r["bonus_reward"]),
        "reason": r["reason"],
        "admin_id": r["admin_id"],
        "created_at": r["created_at"],
    }


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
    reward = float(data.get("reward_usd", data.get("total_score", 0)))  # 兼容旧字段
    with get_conn(db_path) as conn:
        conn.execute(
            "INSERT INTO evaluations(id,task_id,submission_id,reviewer_id,source,rubric_json,total_score,reward_usd,comments,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
            (
                ev_id,
                task_id,
                data["submission_id"],
                data.get("reviewer_id"),
                data.get("source", "human"),
                dumps(data.get("rubric", {})),
                reward,  # total_score 保持兼容
                reward,  # reward_usd 新主字段
                data.get("comments"),
                ts,
            ),
        )
    # 将奖励同步累计到 agent_hub_wallets（通过 agent_id 从 run 查找）
    try:
        sub = get_submission(data["submission_id"], db_path=db_path)
        if sub:
            run = get_run(sub["run_id"], db_path=db_path)
            if run:
                credit_agent_wallet(run["agent_id"], reward, db_path=db_path)
    except Exception:
        pass
    return get_evaluation(ev_id, db_path=db_path)  # type: ignore


def get_evaluation(ev_id: str, db_path=None) -> Optional[Dict[str, Any]]:
    _ensure_schema(db_path)
    with get_conn(db_path) as conn:
        r = conn.execute("SELECT * FROM evaluations WHERE id=?", (ev_id,)).fetchone()
    if not r:
        return None
    # reward_usd 优先，没有该列时回落到 total_score
    keys = r.keys()
    reward = float(r["reward_usd"]) if "reward_usd" in keys else float(r["total_score"])
    return {
        "id": r["id"],
        "task_id": r["task_id"],
        "submission_id": r["submission_id"],
        "reviewer_id": r["reviewer_id"],
        "source": r["source"],
        "rubric": loads(r["rubric_json"], {}),
        "reward_usd": reward,
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
    # 优先使用 reward_usd 列（新版），回落到 total_score（旧版）
    with get_conn(db_path) as conn:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(evaluations)").fetchall()]
        score_col = "reward_usd" if "reward_usd" in cols else "total_score"
        rows = conn.execute(
            f"SELECT submission_id, AVG({score_col}) AS avg_reward_usd, COUNT(*) AS c "
            "FROM evaluations WHERE task_id=? GROUP BY submission_id ORDER BY avg_reward_usd DESC",
            (task_id,),
        ).fetchall()
    return [
        {
            "submission_id": r["submission_id"],
            "avg_reward_usd": float(r["avg_reward_usd"]),
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


# ─── Agent Hub Wallet (Hub 层面奖励追踪) ──────────────────────────────────────

def credit_agent_wallet(agent_id: str, amount_usd: float, db_path=None) -> None:
    """为 Agent 记录一笔奖励收入（Hub 层面）。"""
    _ensure_schema(db_path)
    ts = now_ms()
    with get_conn(db_path) as conn:
        conn.execute(
            """
            INSERT INTO agent_hub_wallets(agent_id, lifetime_earned_usd, updated_at)
            VALUES(?, ?, ?)
            ON CONFLICT(agent_id) DO UPDATE SET
                lifetime_earned_usd = lifetime_earned_usd + ?,
                updated_at = ?
            """,
            (agent_id, amount_usd, ts, amount_usd, ts),
        )


def get_hub_wallet(agent_id: str, db_path=None) -> Dict[str, Any]:
    """获取 Agent 在 Hub 层面记录的累计奖励。"""
    _ensure_schema(db_path)
    with get_conn(db_path) as conn:
        r = conn.execute(
            "SELECT * FROM agent_hub_wallets WHERE agent_id=?", (agent_id,)
        ).fetchone()
    earned = float(r["lifetime_earned_usd"]) if r else 0.0
    return {"agent_id": agent_id, "lifetime_earned_usd": earned}


# ─── Automaton SaaS ─────────────────────────────────────────────────────────

def get_automaton_state(agent_id: str, db_path=None) -> Dict[str, Any]:
    _ensure_schema(db_path)
    with get_conn(db_path) as conn:
        state_row = conn.execute("SELECT * FROM agent_automaton_states WHERE agent_id=?", (agent_id,)).fetchone()
        wallet_row = conn.execute("SELECT * FROM agent_hub_wallets WHERE agent_id=?", (agent_id,)).fetchone()

    state = dict(state_row) if state_row else {
        "agent_id": agent_id,
        "heartbeat_interval_ms": 1800000,
        "consecutive_idles": 0,
        "daily_spent_usd": 0.0,
        "daily_spend_date": "",
    }
    wallet = dict(wallet_row) if wallet_row else {
        "balance_usd": 0.0,
        "lifetime_spent_usd": 0.0,
        "lifetime_earned_usd": 0.0,
        "survival_tier": "normal",
    }
    
    return {**wallet, **state, "agent_id": agent_id}


def update_automaton_state(agent_id: str, updates: Dict[str, Any], db_path=None) -> None:
    _ensure_schema(db_path)
    ts = now_ms()
    with get_conn(db_path) as conn:
        # Initialize rows if not exist
        conn.execute("INSERT OR IGNORE INTO agent_automaton_states (agent_id) VALUES (?)", (agent_id,))
        conn.execute("INSERT OR IGNORE INTO agent_hub_wallets (agent_id) VALUES (?)", (agent_id,))
        
        state_fields = ["heartbeat_interval_ms", "consecutive_idles", "daily_spent_usd", "daily_spend_date"]
        wallet_fields = ["balance_usd", "lifetime_spent_usd", "survival_tier"]
        
        s_clauses, s_params = [], []
        for k in state_fields:
            if k in updates:
                s_clauses.append(f"{k} = ?")
                s_params.append(updates[k])
                
        if s_clauses:
            s_params.append(agent_id)
            conn.execute(f"UPDATE agent_automaton_states SET {', '.join(s_clauses)} WHERE agent_id=?", s_params)
            
        w_clauses, w_params = [], []
        for k in wallet_fields:
            if k in updates:
                w_clauses.append(f"{k} = ?")
                w_params.append(updates[k])
                
        if w_clauses:
            w_params.append(ts)
            w_params.append(agent_id)
            conn.execute(f"UPDATE agent_hub_wallets SET {', '.join(w_clauses)}, updated_at=? WHERE agent_id=?", w_params)


def record_episodic_event(agent_id: str, event_type: str, content: str, db_path=None) -> Dict[str, Any]:
    _ensure_schema(db_path)
    eid = new_id()
    ts = now_ms()
    with get_conn(db_path) as conn:
        conn.execute(
            "INSERT INTO episodic_events(id, agent_id, event_type, content, created_at) VALUES(?,?,?,?,?)",
            (eid, agent_id, event_type, content, ts)
        )
    return {"id": eid, "agent_id": agent_id, "event_type": event_type, "content": content, "created_at": ts}


def get_episodic_events(agent_id: str, event_type: Optional[str] = None, limit: int = 10, db_path=None) -> List[Dict[str, Any]]:
    _ensure_schema(db_path)
    with get_conn(db_path) as conn:
        if event_type:
            rows = conn.execute(
                "SELECT * FROM episodic_events WHERE agent_id=? AND event_type=? ORDER BY created_at DESC LIMIT ?",
                (agent_id, event_type, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM episodic_events WHERE agent_id=? ORDER BY created_at DESC LIMIT ?",
                (agent_id, limit)
            ).fetchall()
    return [dict(r) for r in rows]


def save_procedural_sop(agent_id: str, trigger_condition: str, steps_json: str, db_path=None) -> Dict[str, Any]:
    _ensure_schema(db_path)
    sid = new_id()
    ts = now_ms()
    with get_conn(db_path) as conn:
        conn.execute(
            "INSERT INTO procedural_sops(id, agent_id, trigger_condition, steps_json, created_at, updated_at) VALUES(?,?,?,?,?,?)",
            (sid, agent_id, trigger_condition, steps_json, ts, ts)
        )
    return {"id": sid, "agent_id": agent_id, "trigger_condition": trigger_condition, "steps_json": steps_json, "created_at": ts, "updated_at": ts}


def get_procedural_sops(agent_id: str, db_path=None) -> List[Dict[str, Any]]:
    _ensure_schema(db_path)
    with get_conn(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM procedural_sops WHERE agent_id=? ORDER BY created_at DESC",
            (agent_id,)
        ).fetchall()
    return [dict(r) for r in rows]


def record_soul_history(agent_id: str, field_name: str, old_value: Optional[str], new_value: str, reason: Optional[str], db_path=None) -> Dict[str, Any]:
    _ensure_schema(db_path)
    sid = new_id()
    ts = now_ms()
    with get_conn(db_path) as conn:
        conn.execute(
            "INSERT INTO soul_history(id, agent_id, field_name, old_value, new_value, reason, created_at) VALUES(?,?,?,?,?,?,?)",
            (sid, agent_id, field_name, old_value, new_value, reason, ts)
        )
    return {"id": sid, "agent_id": agent_id, "field_name": field_name, "old_value": old_value, "new_value": new_value, "reason": reason, "created_at": ts}


# ─── Dev Tasks (Run 级别的开发子任务) ─────────────────────────────────────────

def create_dev_task(run_id: str, data: Dict[str, Any], db_path=None) -> Dict[str, Any]:
    """为指定的 Run 创建一个开发子任务。"""
    _ensure_schema(db_path)
    task_id = new_id()
    ts = now_ms()
    with get_conn(db_path) as conn:
        conn.execute(
            "INSERT INTO dev_tasks(id, run_id, title, description, priority, status, created_at, updated_at) VALUES(?,?,?,?,?,?,?,?)",
            (
                task_id,
                run_id,
                data["title"],
                data.get("description"),
                data.get("priority", 3),
                data.get("status", "pending"),
                ts,
                ts,
            ),
        )
    return get_dev_task(task_id, db_path=db_path)


def get_dev_task(task_id: str, db_path=None) -> Optional[Dict[str, Any]]:
    """获取指定开发子任务。"""
    _ensure_schema(db_path)
    with get_conn(db_path) as conn:
        r = conn.execute("SELECT * FROM dev_tasks WHERE id=?", (task_id,)).fetchone()
    if not r:
        return None
    return {
        "id": r["id"],
        "run_id": r["run_id"],
        "title": r["title"],
        "description": r["description"],
        "priority": r["priority"],
        "status": r["status"],
        "created_at": r["created_at"],
        "updated_at": r["updated_at"],
    }


def update_dev_task(task_id: str, patch: Dict[str, Any], db_path=None) -> Optional[Dict[str, Any]]:
    """更新开发子任务。"""
    _ensure_schema(db_path)
    cur = get_dev_task(task_id, db_path=db_path)
    if not cur:
        return None
    ts = now_ms()
    merged = {
        "title": patch.get("title", cur["title"]),
        "description": patch.get("description", cur["description"]),
        "priority": patch.get("priority", cur["priority"]),
        "status": patch.get("status", cur["status"]),
    }
    with get_conn(db_path) as conn:
        conn.execute(
            "UPDATE dev_tasks SET title=?, description=?, priority=?, status=?, updated_at=? WHERE id=?",
            (merged["title"], merged["description"], merged["priority"], merged["status"], ts, task_id),
        )
    return get_dev_task(task_id, db_path=db_path)


def list_dev_tasks_by_run(run_id: str, db_path=None) -> List[Dict[str, Any]]:
    """列出指定 Run 的所有开发子任务。"""
    _ensure_schema(db_path)
    with get_conn(db_path) as conn:
        rows = conn.execute(
            "SELECT id FROM dev_tasks WHERE run_id=? ORDER BY priority ASC, created_at ASC",
            (run_id,),
        ).fetchall()
    return [get_dev_task(r[0], db_path=db_path) for r in rows if r]


def get_dev_task_progress(run_id: str, db_path=None) -> Dict[str, Any]:
    """获取指定 Run 的开发进度统计。"""
    _ensure_schema(db_path)
    with get_conn(db_path) as conn:
        rows = conn.execute(
            "SELECT status, COUNT(*) as count FROM dev_tasks WHERE run_id=? GROUP BY status",
            (run_id,),
        ).fetchall()

    stats = {"pending": 0, "in_progress": 0, "done": 0, "failed": 0}
    total = 0
    for r in rows:
        status = r["status"]
        count = r["count"]
        if status in stats:
            stats[status] = count
        total += count

    progress_pct = round((stats["done"] / total * 100), 1) if total > 0 else 0.0

    return {
        "run_id": run_id,
        "total": total,
        "done": stats["done"],
        "in_progress": stats["in_progress"],
        "pending": stats["pending"],
        "failed": stats["failed"],
        "progress_pct": progress_pct,
    }
