from __future__ import annotations

"""CLI entrypoint for the worker polling loop.

This module provides a small command-line interface for starting the
blocking worker loop defined in :mod:`agent_hub.worker`.

It is intentionally minimal for v0.1:
- Reads batch size and polling interval from CLI flags
- Uses in-memory stub implementations for RunRepository / EventSink / RunExecutor

The goal is to make the worker runnable locally without committing to a
particular DB or event backend yet.
"""

import argparse
import logging
from dataclasses import dataclass, field
from typing import Iterable, List

from .worker import (
    EventSink,
    Run,
    RunExecutor,
    RunRepository,
    RunStatus,
    run_worker_loop,
)

logger = logging.getLogger(__name__)


@dataclass
class InMemoryRunRepository(RunRepository):
    """Very small in-memory repository used for the CLI sandbox.

    This is *not* intended for production use; it only exists so that
    ``agent-hub-worker`` can start up and exercise the polling loop.
    """

    queued: List[Run] = field(default_factory=list)

    def fetch_queued_runs(self, limit: int = 10) -> Iterable[Run]:  # pragma: no cover - trivial
        return list(self.queued[:limit])

    def mark_running(self, run: Run) -> Run:  # pragma: no cover - trivial
        run.status = RunStatus.RUNNING
        return run

    def mark_finished(self, run: Run) -> Run:  # pragma: no cover - trivial
        run.status = RunStatus.FINISHED
        return run

    def mark_failed(self, run: Run, error_message: str) -> Run:  # pragma: no cover - trivial
        run.status = RunStatus.FAILED
        run.error_message = error_message
        return run


class LoggingEventSink(EventSink):
    """Event sink that just logs state transitions.

    This keeps the CLI self-contained while still exercising the
    event-writing surface.
    """

    def write_event(self, *, task_id: str, event_type: str, payload: dict) -> None:  # pragma: no cover - trivial
        logger.info("event[%s] task=%s payload=%s", event_type, task_id, payload)


class NoOpExecutor(RunExecutor):
    """Executor that marks runs as finished without doing real work.

    The real implementation will likely call into an agent runner or
    orchestration layer. For the CLI we only need to exercise the state
    machine.
    """

    def execute(self, run: Run) -> None:  # pragma: no cover - trivial
        logger.info("executing run %s (noop)", run.id)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="OpenClaw Agent Hub worker")
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=5.0,
        help="Polling interval in seconds (default: 5.0)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Maximum number of runs to process per polling cycle (default: 10)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level for the worker process (default: INFO)",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(level=getattr(logging, str(args.log_level).upper(), logging.INFO))

    repo = InMemoryRunRepository()
    events = LoggingEventSink()
    executor = NoOpExecutor()

    run_worker_loop(
        repo=repo,
        events=events,
        executor=executor,
        poll_interval_seconds=args.poll_interval,
        batch_size=args.batch_size,
    )


if __name__ == "__main__":  # pragma: no cover - manual invocation
    main()
