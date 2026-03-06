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


def _v5_rename_score_to_reward_usd(conn):
    """Migration v5: evaluations 表将 total_score 列改名为 reward_usd，
    语义由 '0-100 评分' 改为 'USD 奖励'。"""
    # SQLite 不支持直接 RENAME COLUMN，用 ADD + UPDATE + 旧列保留实现向向展
    try:
        conn.execute("ALTER TABLE evaluations ADD COLUMN reward_usd REAL NOT NULL DEFAULT 0")
        conn.execute("UPDATE evaluations SET reward_usd = total_score")
    except Exception:
        pass  # 列已存在


def _v6_agent_hub_wallets(conn):
    """Migration v6: 新增 agent_hub_wallets 表，用于记录每个 Agent 在 Hub 层面累计奖励与历史花费。"""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS agent_hub_wallets (
            agent_id TEXT PRIMARY KEY,
            lifetime_earned_usd REAL NOT NULL DEFAULT 0.0,  -- 历史累计奖励
            updated_at INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY(agent_id) REFERENCES agents(id) ON DELETE CASCADE
        )
    """)


MIGRATIONS = [
    Migration(version=1, name="init", up=_init_schema),
    Migration(version=2, name="agent_heartbeat", up=_v2_agent_heartbeat),
    Migration(version=3, name="projects_and_ledger", up=_v3_projects_and_ledger),
    Migration(version=4, name="project_takeovers", up=_v4_project_takeovers),
    Migration(version=5, name="rename_score_to_reward_usd", up=_v5_rename_score_to_reward_usd),
    Migration(version=6, name="agent_hub_wallets", up=_v6_agent_hub_wallets),
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
