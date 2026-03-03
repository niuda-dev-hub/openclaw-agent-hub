from __future__ import annotations

"""Minimal worker/poller skeleton for processing queued runs.

This is an initial implementation scaffold for Issue #18:
- Defines RunStatus enum and basic data models
- Provides a synchronous polling loop entrypoint
- Leaves concrete DB and event-writing implementation to future work
"""

import enum
import logging
import time
from dataclasses import dataclass
from typing import Iterable, Optional

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
    """Abstract interface for Run persistence.

    The concrete implementation is expected to handle DB access.
    """

    def fetch_queued_runs(self, limit: int = 10) -> Iterable[Run]:  # pragma: no cover - interface
        raise NotImplementedError

    def mark_running(self, run: Run) -> Run:  # pragma: no cover - interface
        raise NotImplementedError

    def mark_finished(self, run: Run) -> Run:  # pragma: no cover - interface
        raise NotImplementedError

    def mark_failed(self, run: Run, error_message: str) -> Run:  # pragma: no cover - interface
        raise NotImplementedError


class EventSink:
    """Abstract interface for writing audit events.

    Issue #18 requires writing events for state transitions.
    This interface makes it easier to plug in a concrete implementation later.
    """

    def write_event(self, *, task_id: str, event_type: str, payload: dict) -> None:  # pragma: no cover - interface
        raise NotImplementedError


class RunExecutor:
    """Executes a single run.

    For v0.1 this can be as simple as delegating to an agent runner.
    Here we only define the interface and a no-op implementation hook.
    """

    def execute(self, run: Run) -> None:  # pragma: no cover - interface
        """Execute the given run.

        Should raise an exception if execution fails.
        """

        raise NotImplementedError


def process_single_run(*, repo: RunRepository, events: EventSink, executor: RunExecutor, run: Run) -> None:
    """Process a single queued run with basic state transitions.

    queued -> running -> finished/failed
    """

    logger.info("Processing run %s (task=%s)", run.id, run.task_id)

    # queued -> running
    run = repo.mark_running(run)
    events.write_event(
        task_id=run.task_id,
        event_type="run_started",
        payload={"run_id": run.id},
    )

    try:
        executor.execute(run)
    except Exception as exc:  # pragma: no cover - defensive
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
    """Process up to ``batch_size`` queued runs.

    Returns the number of runs processed.
    """

    queued_runs = list(repo.fetch_queued_runs(limit=batch_size))
    if not queued_runs:
        logger.debug("No queued runs found")
        return 0

    for run in queued_runs:
        process_single_run(repo=repo, events=events, executor=executor, run=run)

    return len(queued_runs)


def run_worker_loop(
    *,
    repo: RunRepository,
    events: EventSink,
    executor: RunExecutor,
    poll_interval_seconds: float = 5.0,
    batch_size: int = 10,
) -> None:
    """Blocking polling loop.

    This is intended to be used by a simple CLI entrypoint, e.g.::

        python -m agent_hub.worker

    A more advanced integration (e.g. FastAPI background task) can reuse
    the same ``poll_once`` function.
    """

    logger.info("Starting worker loop (interval=%ss, batch_size=%s)", poll_interval_seconds, batch_size)

    while True:  # pragma: no cover - integration behavior
        processed = poll_once(repo=repo, events=events, executor=executor, batch_size=batch_size)
        if processed == 0:
            logger.debug("Worker idle; sleeping for %ss", poll_interval_seconds)
        time.sleep(poll_interval_seconds)
