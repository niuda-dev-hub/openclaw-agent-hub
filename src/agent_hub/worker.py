from __future__ import annotations

"""Worker/poller for processing queued runs.

Implements v0.1 minimal worker:
- Fetch queued runs from SQLite
- Transition queued -> running -> finished/failed
- Write audit events for each transition

Execution of a run is currently a placeholder (NoopExecutor). This keeps the
state-machine + persistence correct while we wire real agent execution later.
"""

import enum
import logging
import time
from dataclasses import dataclass
from typing import Iterable, Optional

from . import repo as sqlite_repo

logger = logging.getLogger(__name__)


class RunStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    FINISHED = "finished"
    FAILED = "failed"


@dataclass
class Run:
    id: str
    task_id: str
    status: RunStatus
    error_message: Optional[str] = None


class RunRepository:
    """Abstract interface for Run persistence."""

    def fetch_queued_runs(self, limit: int = 10) -> Iterable[Run]:  # pragma: no cover
        raise NotImplementedError

    def mark_running(self, run: Run) -> Run:  # pragma: no cover
        raise NotImplementedError

    def mark_finished(self, run: Run) -> Run:  # pragma: no cover
        raise NotImplementedError

    def mark_failed(self, run: Run, error_message: str) -> Run:  # pragma: no cover
        raise NotImplementedError


class SQLiteRunRepository(RunRepository):
    def __init__(self, db_path=None):
        self.db_path = db_path

    def fetch_queued_runs(self, limit: int = 10) -> Iterable[Run]:
        rows = sqlite_repo.fetch_queued_runs(limit=limit, db_path=self.db_path)
        return [Run(id=r["id"], task_id=r["task_id"], status=RunStatus(r["status"])) for r in rows]

    def mark_running(self, run: Run) -> Run:
        updated = sqlite_repo.mark_run_running(run.id, db_path=self.db_path)
        if not updated:
            return run
        run.status = RunStatus(updated["status"])
        return run

    def mark_finished(self, run: Run) -> Run:
        updated = sqlite_repo.mark_run_finished(run.id, db_path=self.db_path)
        if updated:
            run.status = RunStatus(updated["status"])
        return run

    def mark_failed(self, run: Run, error_message: str) -> Run:
        updated = sqlite_repo.mark_run_failed(run.id, error_message, db_path=self.db_path)
        if updated:
            run.status = RunStatus(updated["status"])
            run.error_message = updated.get("error_message")
        return run


class EventSink:
    """Abstract interface for writing audit events."""

    def write_event(self, *, task_id: str, event_type: str, payload: dict) -> None:  # pragma: no cover
        raise NotImplementedError


class SQLiteEventSink(EventSink):
    def __init__(self, db_path=None):
        self.db_path = db_path

    def write_event(self, *, task_id: str, event_type: str, payload: dict) -> None:
        sqlite_repo.add_event(task_id, event_type, payload=payload, db_path=self.db_path)


class RunExecutor:
    """Executes a single run."""

    def execute(self, run: Run) -> None:  # pragma: no cover
        raise NotImplementedError


class NoopExecutor(RunExecutor):
    """Placeholder executor that always succeeds."""

    def execute(self, run: Run) -> None:
        return


def process_single_run(*, repo: RunRepository, events: EventSink, executor: RunExecutor, run: Run) -> None:
    """Process a single queued run with basic state transitions."""

    logger.info("Processing run %s (task=%s)", run.id, run.task_id)

    # queued -> running
    run = repo.mark_running(run)
    if run.status != RunStatus.RUNNING:
        # someone else likely acquired it
        logger.info("Run %s not acquired (status=%s)", run.id, run.status)
        return

    events.write_event(
        task_id=run.task_id,
        event_type="run_started",
        payload={"run_id": run.id},
    )

    try:
        executor.execute(run)
    except Exception as exc:  # pragma: no cover
        logger.exception("Run %s failed", run.id)
        run = repo.mark_failed(run, error_message=str(exc))
        events.write_event(
            task_id=run.task_id,
            event_type="run_failed",
            payload={"run_id": run.id, "error_message": str(exc)},
        )
        return

    run = repo.mark_finished(run)
    events.write_event(
        task_id=run.task_id,
        event_type="run_finished",
        payload={"run_id": run.id},
    )


def poll_once(*, repo: RunRepository, events: EventSink, executor: RunExecutor, batch_size: int = 10) -> int:
    queued_runs = list(repo.fetch_queued_runs(limit=batch_size))
    if not queued_runs:
        logger.debug("No queued runs found")
        return 0

    processed = 0
    for run in queued_runs:
        before = run.status
        process_single_run(repo=repo, events=events, executor=executor, run=run)
        # best-effort count: if it was queued we attempted it
        if before == RunStatus.QUEUED:
            processed += 1

    return processed


def run_worker_loop(
    *,
    repo: RunRepository,
    events: EventSink,
    executor: RunExecutor,
    poll_interval_seconds: float = 5.0,
    batch_size: int = 10,
) -> None:
    logger.info("Starting worker loop (interval=%ss, batch_size=%s)", poll_interval_seconds, batch_size)

    while True:  # pragma: no cover
        processed = poll_once(repo=repo, events=events, executor=executor, batch_size=batch_size)
        if processed == 0:
            logger.debug("Worker idle; sleeping for %ss", poll_interval_seconds)
        time.sleep(poll_interval_seconds)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    repo = SQLiteRunRepository()
    events = SQLiteEventSink()
    executor = NoopExecutor()
    run_worker_loop(repo=repo, events=events, executor=executor)


if __name__ == "__main__":
    main()
