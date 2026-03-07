from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
from supabase import create_client, Client

from ..utils import now_ms, new_id, dumps, loads

_url: str = os.getenv("SUPABASE_URL", "")
_key: str = os.getenv("SUPABASE_KEY", "")

supabase: Optional[Client] = None
if _url and _key:
    supabase = create_client(_url, _key)

def _get_client() -> Client:
    if not supabase:
        raise RuntimeError("SUPABASE_URL or SUPABASE_KEY is missing. Cannot use Supabase repo.")
    return supabase

# ==============================================================================
# Helper for parsing json text fields (compatible with the text fields we had)
# ==============================================================================
def _parse_json_field(val: Any) -> Any:
    if isinstance(val, str):
        return loads(val, {})
    # If supabase column is jsonb, it returns dict natively
    return val or {}


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
    lid = entry_id or new_id()
    ts = now_ms()
    rec = {
        "id": lid,
        "actor_type": actor_type,
        "actor_id": actor_id,
        "delta": int(delta),
        "event_type": event_type,
        "ref_type": ref_type,
        "ref_id": ref_id,
        "meta_json": dumps(meta or {}),
        "created_at": ts
    }
    _get_client().table("points_ledger").insert(rec).execute()
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
    res = _get_client().table("points_ledger").select("delta").eq("actor_type", actor_type).eq("actor_id", actor_id).execute()
    return sum(int(r["delta"]) for r in res.data)

def create_project(data: Dict[str, Any], db_path=None) -> Dict[str, Any]:
    pid = new_id()
    ts = now_ms()
    rec = {
        "id": pid,
        "title": data["title"],
        "description": data.get("description"),
        "publisher_type": data.get("publisher_type", "agent"),
        "publisher_id": data["publisher_id"],
        "stake_points": int(data.get("stake_points", 0)),
        "status": data.get("status", "active"),
        "created_at": ts,
        "updated_at": ts,
    }
    _get_client().table("projects").insert(rec).execute()
    return get_project(pid, db_path=db_path)  # type: ignore

def get_project(project_id: str, db_path=None) -> Optional[Dict[str, Any]]:
    res = _get_client().table("projects").select("*").eq("id", project_id).execute()
    if not res.data:
        return None
    r = res.data[0]
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
    # Check if existing
    ex = _get_client().table("project_takeovers").select("*").eq("project_id", project_id).execute()
    if ex.data:
        r = ex.data[0]
        return r  # simplified return to avoid redundant mapping

    proj = get_project(project_id)
    if not proj:
        raise KeyError("project_not_found")
    
    from_pt = proj["publisher_type"]
    from_pid = proj["publisher_id"]
    stake = proj["stake_points"]
    ts = now_ms()

    def _eid(suffix: str) -> str:
        if not idempotency_key:
            return new_id()
        return f"takeover:{project_id}:{idempotency_key}:{suffix}"

    if stake > 0:
        add_ledger_entry(from_pt, from_pid, stake, "PROJECT_STAKE_REFUND", "project", project_id, {"reason": "admin_takeover_refund"}, entry_id=_eid("stake_refund"))
    
    b = int(bonus_reward or 0)
    if b < 0:
        raise ValueError("bonus_reward_must_be_non_negative")
    if b > 0:
        add_ledger_entry("system", "treasury", -b, "TREASURY_MINT_OUT", "project", project_id, {"to": f"{from_pt}:{from_pid}"}, entry_id=_eid("treasury_out"))
        add_ledger_entry(from_pt, from_pid, b, "PROJECT_IDEA_BONUS", "project", project_id, {"admin_id": admin_id, "reason": reason or ""}, entry_id=_eid("bonus"))

    _get_client().table("projects").update({
        "publisher_type": "admin",
        "publisher_id": admin_id,
        "stake_points": 0,
        "updated_at": ts
    }).eq("id", project_id).execute()

    takeover_rec = {
        "id": _eid("record"),
        "project_id": project_id,
        "from_publisher_type": from_pt,
        "from_publisher_id": from_pid,
        "to_publisher_type": "admin",
        "to_publisher_id": admin_id,
        "stake_refund": stake,
        "bonus_reward": b,
        "reason": reason,
        "admin_id": admin_id,
        "created_at": ts
    }
    _get_client().table("project_takeovers").insert(takeover_rec).execute()
    return takeover_rec


def _ensure_schema(db_path=None) -> None:
    # Scheme migrations should be handled via Supabase dashboard / CLI explicitly.
    pass


def create_agent(data: Dict[str, Any], db_path=None) -> Dict[str, Any]:
    agent_id = new_id()
    ts = now_ms()
    rec = {
        "id": agent_id,
        "name": data["name"],
        "description": data.get("description"),
        "agent_type": data.get("agent_type", "openclaw"),
        "config_json": dumps(data.get("config", {})),
        "is_enabled": 1,
        "created_at": ts,
    }
    _get_client().table("agents").insert(rec).execute()
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
    res = _get_client().table("agents").select("*").order("created_at", desc=True).execute()
    return [{
        "id": r["id"],
        "name": r["name"],
        "description": r["description"],
        "agent_type": r["agent_type"],
        "config": _parse_json_field(r["config_json"]),
        "is_enabled": bool(r["is_enabled"]),
        "created_at": r["created_at"],
        "last_heartbeat_at": r.get("last_heartbeat_at")
    } for r in res.data]


def get_agent(agent_id: str, db_path=None) -> Optional[Dict[str, Any]]:
    res = _get_client().table("agents").select("*").eq("id", agent_id).execute()
    if not res.data:
        return None
    r = res.data[0]
    return {
        "id": r["id"],
        "name": r["name"],
        "description": r["description"],
        "agent_type": r["agent_type"],
        "config": _parse_json_field(r["config_json"]),
        "is_enabled": bool(r["is_enabled"]),
        "created_at": r["created_at"],
        "last_heartbeat_at": r.get("last_heartbeat_at")
    }

def update_agent(agent_id: str, patch: Dict[str, Any], db_path=None) -> Optional[Dict[str, Any]]:
    cur = get_agent(agent_id)
    if not cur:
        return None
    rec_update = {}
    if "description" in patch:
        rec_update["description"] = patch["description"]
    if "config" in patch:
        rec_update["config_json"] = dumps(patch["config"])
    if "is_enabled" in patch:
        rec_update["is_enabled"] = 1 if patch["is_enabled"] else 0
        
    if rec_update:
        _get_client().table("agents").update(rec_update).eq("id", agent_id).execute()
    return get_agent(agent_id)


def create_task(data: Dict[str, Any], db_path=None) -> Dict[str, Any]:
    task_id = new_id()
    ts = now_ms()
    rec = {
        "id": task_id,
        "title": data["title"],
        "prompt": data["prompt"],
        "input_json": dumps(data.get("input", {})),
        "constraints_json": dumps(data.get("constraints", {})),
        "expected_output_type": data.get("expected_output_type", "text"),
        "status": data.get("status", "draft"),
        "created_by": data.get("created_by"),
        "created_at": ts,
        "updated_at": ts,
    }
    _get_client().table("tasks").insert(rec).execute()
    return get_task(task_id, db_path=db_path)  # type: ignore

def get_task(task_id: str, db_path=None) -> Optional[Dict[str, Any]]:
    res = _get_client().table("tasks").select("*").eq("id", task_id).execute()
    if not res.data:
        return None
    r = res.data[0]
    return {
        "id": r["id"],
        "title": r["title"],
        "prompt": r["prompt"],
        "input": _parse_json_field(r["input_json"]),
        "constraints": _parse_json_field(r["constraints_json"]),
        "expected_output_type": r["expected_output_type"],
        "status": r["status"],
        "created_by": r["created_by"],
        "created_at": r["created_at"],
        "updated_at": r["updated_at"],
    }


def list_tasks(status: Optional[str] = None, db_path=None) -> List[Dict[str, Any]]:
    q = _get_client().table("tasks").select("id").order("created_at", desc=True)
    if status:
        q = q.eq("status", status)
    res = q.execute()
    return [get_task(r["id"]) for r in res.data if r]  # type: ignore


def update_task(task_id: str, patch: Dict[str, Any], db_path=None) -> Optional[Dict[str, Any]]:
    cur = get_task(task_id)
    if not cur:
        return None
    ts = now_ms()
    rec = {"updated_at": ts}
    if "title" in patch: rec["title"] = patch["title"]
    if "prompt" in patch: rec["prompt"] = patch["prompt"]
    if "input" in patch: rec["input_json"] = dumps(patch["input"])
    if "constraints" in patch: rec["constraints_json"] = dumps(patch["constraints"])
    if "expected_output_type" in patch: rec["expected_output_type"] = patch["expected_output_type"]
    if "status" in patch: rec["status"] = patch["status"]
    
    _get_client().table("tasks").update(rec).eq("id", task_id).execute()
    return get_task(task_id)


def create_runs(task_id: str, agent_ids: List[str], run_params: Dict[str, Any], db_path=None) -> List[Dict[str, Any]]:
    ts = now_ms()
    run_ids = []
    recs = []
    for aid in agent_ids:
        run_id = new_id()
        recs.append({
            "id": run_id,
            "task_id": task_id,
            "agent_id": aid,
            "status": "queued",
            "queued_at": ts,
            "run_params_json": dumps(run_params)
        })
        run_ids.append(run_id)
    if recs:
        _get_client().table("runs").insert(recs).execute()
    
    return [get_run(rid) for rid in run_ids if rid] # type: ignore


def fetch_queued_runs(limit: int = 10, db_path=None) -> List[Dict[str, Any]]:
    res = _get_client().table("runs").select("id").eq("status", "queued").order("queued_at", desc=False).limit(limit).execute()
    return [get_run(r["id"]) for r in res.data if r] # type: ignore


def mark_run_running(run_id: str, db_path=None) -> Optional[Dict[str, Any]]:
    ts = now_ms()
    # supabase Python SDK doesn't natively return row count easily on update without returning=minimal,
    # we just update where status='queued'
    _get_client().table("runs").update({"status":"running", "started_at":ts, "error_message":None}).eq("id", run_id).eq("status", "queued").execute()
    return get_run(run_id)

def mark_run_finished(run_id: str, usage: Dict[str, Any] | None = None, db_path=None) -> Optional[Dict[str, Any]]:
    ts = now_ms()
    _get_client().table("runs").update({"status":"finished", "finished_at":ts, "usage_json":dumps(usage or {})}).eq("id", run_id).execute()
    return get_run(run_id)

def mark_run_failed(run_id: str, error_message: str, db_path=None) -> Optional[Dict[str, Any]]:
    ts = now_ms()
    _get_client().table("runs").update({"status":"failed", "finished_at":ts, "error_message":error_message}).eq("id", run_id).execute()
    return get_run(run_id)

def get_active_run_for_agent(task_id: str, agent_id: str, db_path=None) -> Optional[Dict[str, Any]]:
    res = _get_client().table("runs").select("id").eq("task_id", task_id).eq("agent_id", agent_id).in_("status", ["queued", "running"]).order("queued_at", desc=True).limit(1).execute()
    if not res.data:
        return None
    return get_run(res.data[0]["id"])

def list_participants(task_id: str, db_path=None) -> List[Dict[str, Any]]:
    # Without group by natively via REST easily, we select all for this task and aggr locally. (Fine for now).
    res = _get_client().table("runs").select("agent_id, status, queued_at").eq("task_id", task_id).execute()
    aggr = {}
    for r in res.data:
        aid = r["agent_id"]
        if aid not in aggr:
            aggr[aid] = {"runs_count": 0, "last_queued": 0, "latest_status": None}
        aggr[aid]["runs_count"] += 1
        if r["queued_at"] and r["queued_at"] > aggr[aid]["last_queued"]:
            aggr[aid]["last_queued"] = r["queued_at"]
            aggr[aid]["latest_status"] = r["status"]
            
    out = []
    for aid, st in aggr.items():
        a = get_agent(aid)
        out.append({
            "agent_id": aid,
            "agent_name": a["name"] if a else None,
            "latest_status": st["latest_status"],
            "runs_count": st["runs_count"]
        })
    return sorted(out, key=lambda x: x["runs_count"], reverse=True)


def list_runs(task_id: str, db_path=None) -> List[Dict[str, Any]]:
    res = _get_client().table("runs").select("id").eq("task_id", task_id).order("queued_at", desc=False).execute()
    return [get_run(r["id"]) for r in res.data if r] # type: ignore


def get_run(run_id: str, db_path=None) -> Optional[Dict[str, Any]]:
    res = _get_client().table("runs").select("*").eq("id", run_id).execute()
    if not res.data:
        return None
    r = res.data[0]
    return {
        "id": r["id"],
        "task_id": r["task_id"],
        "agent_id": r["agent_id"],
        "status": r["status"],
        "queued_at": r["queued_at"],
        "started_at": r.get("started_at"),
        "finished_at": r.get("finished_at"),
        "run_params": _parse_json_field(r.get("run_params_json")),
        "usage": _parse_json_field(r.get("usage_json")),
        "error_message": r.get("error_message"),
    }

def create_submission(run_id: str, data: Dict[str, Any], db_path=None) -> Dict[str, Any]:
    sub_id = new_id()
    ts = now_ms()
    run = get_run(run_id)
    if not run:
        raise KeyError("run_not_found")
    rec = {
        "id": sub_id,
        "run_id": run_id,
        "task_id": run["task_id"],
        "content_type": data.get("content_type", "text"),
        "content": data["content"],
        "attachments_json": dumps(data.get("attachments", [])),
        "summary": data.get("summary"),
        "created_at": ts
    }
    _get_client().table("submissions").insert(rec).execute()
    return get_submission(sub_id) # type: ignore

def get_submission(submission_id: str, db_path=None) -> Optional[Dict[str, Any]]:
    res = _get_client().table("submissions").select("*").eq("id", submission_id).execute()
    if not res.data:
        return None
    r = res.data[0]
    return {
        "id": r["id"],
        "run_id": r["run_id"],
        "task_id": r["task_id"],
        "content_type": r["content_type"],
        "content": r["content"],
        "attachments": _parse_json_field(r.get("attachments_json")),
        "summary": r.get("summary"),
        "created_at": r["created_at"],
    }

def list_submissions(task_id: str, db_path=None) -> List[Dict[str, Any]]:
    res = _get_client().table("submissions").select("id").eq("task_id", task_id).order("created_at", desc=True).execute()
    return [get_submission(r["id"]) for r in res.data if r] # type: ignore

def create_evaluation(task_id: str, data: Dict[str, Any], db_path=None) -> Dict[str, Any]:
    ev_id = new_id()
    ts = now_ms()
    reward = float(data.get("reward_usd", data.get("total_score", 0)))
    rec = {
        "id": ev_id,
        "task_id": task_id,
        "submission_id": data["submission_id"],
        "reviewer_id": data.get("reviewer_id"),
        "source": data.get("source", "human"),
        "rubric_json": dumps(data.get("rubric", {})),
        "total_score": reward,
        "reward_usd": reward,
        "comments": data.get("comments"),
        "created_at": ts
    }
    _get_client().table("evaluations").insert(rec).execute()
    
    try:
        sub = get_submission(data["submission_id"])
        if sub:
            run = get_run(sub["run_id"])
            if run:
                credit_agent_wallet(run["agent_id"], reward)
    except Exception:
        pass
    return get_evaluation(ev_id) # type: ignore

def get_evaluation(ev_id: str, db_path=None) -> Optional[Dict[str, Any]]:
    res = _get_client().table("evaluations").select("*").eq("id", ev_id).execute()
    if not res.data:
        return None
    r = res.data[0]
    reward = float(r.get("reward_usd", r.get("total_score", 0)))
    return {
        "id": r["id"],
        "task_id": r["task_id"],
        "submission_id": r["submission_id"],
        "reviewer_id": r["reviewer_id"],
        "source": r["source"],
        "rubric": _parse_json_field(r.get("rubric_json")),
        "reward_usd": reward,
        "comments": r.get("comments"),
        "created_at": r["created_at"],
    }

def list_evaluations(task_id: str, db_path=None) -> List[Dict[str, Any]]:
    res = _get_client().table("evaluations").select("id").eq("task_id", task_id).order("created_at", desc=True).execute()
    return [get_evaluation(r["id"]) for r in res.data if r] # type: ignore

def leaderboard(task_id: str, db_path=None) -> List[Dict[str, Any]]:
    res = _get_client().table("evaluations").select("submission_id, reward_usd, total_score").eq("task_id", task_id).execute()
    aggr = {}
    for r in res.data:
        sid = r["submission_id"]
        v = float(r.get("reward_usd", r.get("total_score", 0)))
        if sid not in aggr:
            aggr[sid] = {"sum": 0.0, "c": 0}
        aggr[sid]["sum"] += v
        aggr[sid]["c"] += 1
    
    out = []
    for sid, st in aggr.items():
        out.append({
            "submission_id": sid,
            "avg_reward_usd": st["sum"] / st["c"],
            "review_count": st["c"]
        })
    return sorted(out, key=lambda x: x["avg_reward_usd"], reverse=True)


def set_decision(task_id: str, data: Dict[str, Any], db_path=None) -> Dict[str, Any]:
    dec_id = new_id()
    ts = now_ms()
    rec = {
        "id": dec_id,
        "task_id": task_id,
        "winner_submission_id": data["winner_submission_id"],
        "decided_by": data.get("decided_by"),
        "rationale": data.get("rationale"),
        "created_at": ts
    }
    _get_client().table("decisions").insert(rec).execute()
    return get_decision(task_id) # type: ignore

def get_decision(task_id: str, db_path=None) -> Optional[Dict[str, Any]]:
    res = _get_client().table("decisions").select("*").eq("task_id", task_id).execute()
    if not res.data:
        return None
    r = res.data[0]
    return r

def add_event(task_id: str | None, event_type: str, actor_type: str = "system", actor_id: str | None = None, payload: Dict[str, Any] | None = None, db_path=None) -> None:
    ev_id = new_id()
    ts = now_ms()
    rec = {
        "id": ev_id,
        "task_id": task_id,
        "event_type": event_type,
        "actor_type": actor_type,
        "actor_id": actor_id,
        "payload_json": dumps(payload or {}),
        "created_at": ts
    }
    _get_client().table("events").insert(rec).execute()

def list_events(task_id: str, limit: int = 50, db_path=None) -> List[Dict[str, Any]]:
    res = _get_client().table("events").select("*").eq("task_id", task_id).order("created_at", desc=True).limit(limit).execute()
    return [{
        "id": r["id"],
        "task_id": r["task_id"],
        "event_type": r["event_type"],
        "actor_type": r["actor_type"],
        "actor_id": r["actor_id"],
        "payload": _parse_json_field(r.get("payload_json")),
        "created_at": r["created_at"],
    } for r in res.data]

def update_agent_heartbeat(agent_id: str, db_path=None) -> Optional[Dict[str, Any]]:
    _get_client().table("agents").update({"last_heartbeat_at": now_ms()}).eq("id", agent_id).execute()
    return get_agent(agent_id)

# ─── Hub Wallet & Automaton SaaS ───────────────────────────────────────────

def credit_agent_wallet(agent_id: str, amount_usd: float, db_path=None) -> None:
    cli = _get_client()
    ex = cli.table("agent_hub_wallets").select("lifetime_earned_usd").eq("agent_id", agent_id).execute()
    ts = now_ms()
    if ex.data:
        new_earned = float(ex.data[0]["lifetime_earned_usd"]) + amount_usd
        cli.table("agent_hub_wallets").update({"lifetime_earned_usd": new_earned, "updated_at": ts}).eq("agent_id", agent_id).execute()
    else:
        cli.table("agent_hub_wallets").insert({"agent_id": agent_id, "lifetime_earned_usd": amount_usd, "updated_at": ts}).execute()

def get_hub_wallet(agent_id: str, db_path=None) -> Dict[str, Any]:
    res = _get_client().table("agent_hub_wallets").select("*").eq("agent_id", agent_id).execute()
    earned = float(res.data[0]["lifetime_earned_usd"]) if res.data else 0.0
    return {"agent_id": agent_id, "lifetime_earned_usd": earned}

def get_automaton_state(agent_id: str, db_path=None) -> Dict[str, Any]:
    state_res = _get_client().table("agent_automaton_states").select("*").eq("agent_id", agent_id).execute()
    wallet_res = _get_client().table("agent_hub_wallets").select("*").eq("agent_id", agent_id).execute()
    
    s = state_res.data[0] if state_res.data else {
        "heartbeat_interval_ms": 1800000,
        "consecutive_idles": 0,
        "daily_spent_usd": 0.0,
        "daily_spend_date": "",
    }
    w = wallet_res.data[0] if wallet_res.data else {
        "balance_usd": 0.0,
        "lifetime_spent_usd": 0.0,
        "lifetime_earned_usd": 0.0,
        "survival_tier": "normal",
    }
    return {**w, **s, "agent_id": agent_id}

def update_automaton_state(agent_id: str, updates: Dict[str, Any], db_path=None) -> None:
    cli = _get_client()
    ts = now_ms()
    state_fields = ["heartbeat_interval_ms", "consecutive_idles", "daily_spent_usd", "daily_spend_date"]
    wallet_fields = ["balance_usd", "lifetime_spent_usd", "survival_tier"]
    
    s_updates = {k: updates[k] for k in state_fields if k in updates}
    if s_updates:
        if not cli.table("agent_automaton_states").select("agent_id").eq("agent_id", agent_id).execute().data:
            cli.table("agent_automaton_states").insert({"agent_id": agent_id, **s_updates}).execute()
        else:
            cli.table("agent_automaton_states").update(s_updates).eq("agent_id", agent_id).execute()
            
    w_updates = {k: updates[k] for k in wallet_fields if k in updates}
    if w_updates:
        w_updates["updated_at"] = ts
        if not cli.table("agent_hub_wallets").select("agent_id").eq("agent_id", agent_id).execute().data:
            cli.table("agent_hub_wallets").insert({"agent_id": agent_id, "lifetime_earned_usd": 0.0, **w_updates}).execute()
        else:
            cli.table("agent_hub_wallets").update(w_updates).eq("agent_id", agent_id).execute()

def record_episodic_event(agent_id: str, event_type: str, content: str, db_path=None) -> Dict[str, Any]:
    eid = new_id()
    ts = now_ms()
    rec = {"id": eid, "agent_id": agent_id, "event_type": event_type, "content": content, "created_at": ts}
    _get_client().table("episodic_events").insert(rec).execute()
    return rec

def get_episodic_events(agent_id: str, event_type: Optional[str] = None, limit: int = 10, db_path=None) -> List[Dict[str, Any]]:
    q = _get_client().table("episodic_events").select("*").eq("agent_id", agent_id)
    if event_type:
        q = q.eq("event_type", event_type)
    res = q.order("created_at", desc=True).limit(limit).execute()
    return res.data

def save_procedural_sop(agent_id: str, trigger_condition: str, steps_json: str, db_path=None) -> Dict[str, Any]:
    sid = new_id()
    ts = now_ms()
    rec = {"id": sid, "agent_id": agent_id, "trigger_condition": trigger_condition, "steps_json": steps_json, "created_at": ts, "updated_at": ts}
    _get_client().table("procedural_sops").insert(rec).execute()
    return rec

def get_procedural_sops(agent_id: str, db_path=None) -> List[Dict[str, Any]]:
    res = _get_client().table("procedural_sops").select("*").eq("agent_id", agent_id).order("created_at", desc=True).execute()
    return res.data

def record_soul_history(agent_id: str, field_name: str, old_value: Optional[str], new_value: str, reason: Optional[str], db_path=None) -> Dict[str, Any]:
    sid = new_id()
    ts = now_ms()
    rec = {"id": sid, "agent_id": agent_id, "field_name": field_name, "old_value": old_value, "new_value": new_value, "reason": reason, "created_at": ts}
    _get_client().table("soul_history").insert(rec).execute()
    return rec


# ─── Dev Tasks (Run 级别的开发子任务) ─────────────────────────────────────────

def create_dev_task(run_id: str, data: Dict[str, Any], db_path=None) -> Dict[str, Any]:
    """为指定的 Run 创建一个开发子任务。"""
    task_id = new_id()
    ts = now_ms()
    rec = {
        "id": task_id,
        "run_id": run_id,
        "title": data["title"],
        "description": data.get("description"),
        "priority": data.get("priority", 3),
        "status": data.get("status", "pending"),
        "created_at": ts,
        "updated_at": ts,
    }
    _get_client().table("dev_tasks").insert(rec).execute()
    return get_dev_task(task_id, db_path=db_path)


def get_dev_task(task_id: str, db_path=None) -> Optional[Dict[str, Any]]:
    """获取指定开发子任务。"""
    res = _get_client().table("dev_tasks").select("*").eq("id", task_id).execute()
    if not res.data:
        return None
    r = res.data[0]
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
    cur = get_dev_task(task_id, db_path=db_path)
    if not cur:
        return None
    ts = now_ms()
    rec = {"updated_at": ts}
    if "title" in patch:
        rec["title"] = patch["title"]
    if "description" in patch:
        rec["description"] = patch["description"]
    if "priority" in patch:
        rec["priority"] = patch["priority"]
    if "status" in patch:
        rec["status"] = patch["status"]

    _get_client().table("dev_tasks").update(rec).eq("id", task_id).execute()
    return get_dev_task(task_id, db_path=db_path)


def list_dev_tasks_by_run(run_id: str, db_path=None) -> List[Dict[str, Any]]:
    """列出指定 Run 的所有开发子任务。"""
    res = _get_client().table("dev_tasks").select("id").eq("run_id", run_id).order("priority", desc=False).order("created_at", desc=False).execute()
    return [get_dev_task(r["id"], db_path=db_path) for r in res.data if r]


def get_dev_task_progress(run_id: str, db_path=None) -> Dict[str, Any]:
    """获取指定 Run 的开发进度统计。"""
    res = _get_client().table("dev_tasks").select("status").eq("run_id", run_id).execute()

    stats = {"pending": 0, "in_progress": 0, "done": 0, "failed": 0}
    total = 0
    for r in res.data:
        status = r["status"]
        if status in stats:
            stats[status] += 1
        total += 1

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
