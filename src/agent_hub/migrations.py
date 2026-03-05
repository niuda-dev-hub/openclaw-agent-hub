from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .db import get_conn


@dataclass
class Migration:
    version: int
    name: str
    up: Callable


def _init_schema(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS meta (
          key TEXT PRIMARY KEY,
          value TEXT
        );
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS agents (
          id TEXT PRIMARY KEY,
          name TEXT NOT NULL,
          description TEXT,
          agent_type TEXT NOT NULL,
          config_json TEXT,
          is_enabled INTEGER NOT NULL DEFAULT 1,
          created_at INTEGER NOT NULL
        );
        """
    )
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_agents_name ON agents(name);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_agents_enabled ON agents(is_enabled);")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
          id TEXT PRIMARY KEY,
          title TEXT NOT NULL,
          prompt TEXT NOT NULL,
          input_json TEXT,
          constraints_json TEXT,
          expected_output_type TEXT NOT NULL,
          status TEXT NOT NULL,
          created_by TEXT,
          created_at INTEGER NOT NULL,
          updated_at INTEGER NOT NULL
        );
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_created_by ON tasks(created_by);")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS runs (
          id TEXT PRIMARY KEY,
          task_id TEXT NOT NULL,
          agent_id TEXT NOT NULL,
          status TEXT NOT NULL,
          queued_at INTEGER,
          started_at INTEGER,
          finished_at INTEGER,
          run_params_json TEXT,
          usage_json TEXT,
          error_message TEXT,
          FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE,
          FOREIGN KEY(agent_id) REFERENCES agents(id) ON DELETE RESTRICT
        );
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_runs_task ON runs(task_id);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_runs_agent ON runs(agent_id);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_runs_task_status ON runs(task_id, status);")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS submissions (
          id TEXT PRIMARY KEY,
          run_id TEXT NOT NULL,
          task_id TEXT NOT NULL,
          content_type TEXT NOT NULL,
          content TEXT NOT NULL,
          attachments_json TEXT,
          summary TEXT,
          created_at INTEGER NOT NULL,
          FOREIGN KEY(run_id) REFERENCES runs(id) ON DELETE CASCADE,
          FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE
        );
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_submissions_task ON submissions(task_id);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_submissions_run ON submissions(run_id);")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS evaluations (
          id TEXT PRIMARY KEY,
          task_id TEXT NOT NULL,
          submission_id TEXT NOT NULL,
          reviewer_id TEXT,
          source TEXT NOT NULL,
          rubric_json TEXT,
          total_score REAL NOT NULL,
          comments TEXT,
          created_at INTEGER NOT NULL,
          FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE,
          FOREIGN KEY(submission_id) REFERENCES submissions(id) ON DELETE CASCADE
        );
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_evals_task ON evaluations(task_id);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_evals_submission ON evaluations(submission_id);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_evals_task_submission ON evaluations(task_id, submission_id);")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS decisions (
          id TEXT PRIMARY KEY,
          task_id TEXT NOT NULL UNIQUE,
          winner_submission_id TEXT NOT NULL,
          decided_by TEXT,
          rationale TEXT,
          created_at INTEGER NOT NULL,
          FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE,
          FOREIGN KEY(winner_submission_id) REFERENCES submissions(id) ON DELETE RESTRICT
        );
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
          id TEXT PRIMARY KEY,
          task_id TEXT,
          event_type TEXT NOT NULL,
          actor_type TEXT NOT NULL,
          actor_id TEXT,
          payload_json TEXT,
          created_at INTEGER NOT NULL,
          FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE
        );
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_events_task ON events(task_id);")


def _v2_agent_heartbeat(conn):
    """Migration v2: 给 agents 表添加 last_heartbeat_at 列，用于心跳/在线状态。"""
    # 如果列已存在则忽略错误（SQLite 不支持 IF NOT EXISTS for column）
    try:
        conn.execute("ALTER TABLE agents ADD COLUMN last_heartbeat_at INTEGER")
    except Exception:
        pass  # 列已存在，忽略


def _v3_projects_and_ledger(conn):
    """Migration v3: add projects + points ledger tables (foundation for incentives)."""

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS projects (
          id TEXT PRIMARY KEY,
          title TEXT NOT NULL,
          description TEXT,
          publisher_type TEXT NOT NULL,
          publisher_id TEXT NOT NULL,
          stake_points INTEGER NOT NULL DEFAULT 0,
          status TEXT NOT NULL DEFAULT 'active',
          created_at INTEGER NOT NULL,
          updated_at INTEGER NOT NULL
        );
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_projects_publisher ON projects(publisher_type, publisher_id);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);")

    # Append-only ledger: balance = SUM(delta)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS points_ledger (
          id TEXT PRIMARY KEY,
          actor_type TEXT NOT NULL,
          actor_id TEXT NOT NULL,
          delta INTEGER NOT NULL,
          event_type TEXT NOT NULL,
          ref_type TEXT,
          ref_id TEXT,
          meta_json TEXT,
          created_at INTEGER NOT NULL
        );
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ledger_actor ON points_ledger(actor_type, actor_id);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ledger_ref ON points_ledger(ref_type, ref_id);")


def _v4_project_takeovers(conn):
    """Migration v4: admin project takeover records (publisher transfer + stake refund + bonus)."""

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS project_takeovers (
          id TEXT PRIMARY KEY,
          project_id TEXT NOT NULL UNIQUE,
          from_publisher_type TEXT,
          from_publisher_id TEXT,
          to_publisher_type TEXT,
          to_publisher_id TEXT,
          stake_refund INTEGER NOT NULL DEFAULT 0,
          bonus_reward INTEGER NOT NULL DEFAULT 0,
          reason TEXT,
          admin_id TEXT,
          created_at INTEGER NOT NULL
        );
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_takeovers_project ON project_takeovers(project_id);")


MIGRATIONS = [
    Migration(version=1, name="init", up=_init_schema),
    Migration(version=2, name="agent_heartbeat", up=_v2_agent_heartbeat),
    Migration(version=3, name="projects_and_ledger", up=_v3_projects_and_ledger),
    Migration(version=4, name="project_takeovers", up=_v4_project_takeovers),
]


def _get_version(conn) -> int:
    # meta table may not exist on first run
    try:
        row = conn.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()
    except Exception:
        return 0
    if not row:
        return 0
    try:
        return int(row[0])
    except Exception:
        return 0


def _set_version(conn, v: int) -> None:
    conn.execute(
        "INSERT INTO meta(key,value) VALUES('schema_version', ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (str(v),),
    )


def migrate(db_path=None) -> int:
    with get_conn(db_path) as conn:
        cur = _get_version(conn)
        for m in MIGRATIONS:
            if m.version > cur:
                m.up(conn)
                _set_version(conn, m.version)
                cur = m.version
        return cur
