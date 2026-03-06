from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Iterator


def _default_db_path() -> Path:
    # Local-first, cloud-ready: keep data dir configurable
    base = os.getenv("AGENT_HUB_DATA_DIR")
    if base:
        return Path(base) / "agent-hub.db"
    return Path.home() / ".openclaw-agent-hub" / "agent-hub.db"


def ensure_db_dir(db_path: Path | str) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)


@contextmanager
def get_conn(db_path: Path | None = None) -> Iterator[sqlite3.Connection]:
    path = db_path or _default_db_path()
    ensure_db_dir(path)

    conn = sqlite3.connect(str(path))
    try:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON;")
        # WAL improves concurrency for read-heavy access
        conn.execute("PRAGMA journal_mode=WAL;")
        yield conn
        conn.commit()
    finally:
        conn.close()
