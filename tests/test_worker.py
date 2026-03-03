from __future__ import annotations

from typing import List

from agent_hub.worker import (
    EventSink,
    Run,
    RunExecutor,
    RunRepository,
    RunStatus,
    poll_once,
    process_single_run,
)


class InMemoryRunRepo(RunRepository):
    def __init__(self, runs: List[Run]):
        self.runs = {r.id: r for r in runs}

    def fetch_queued_runs(self, limit: int = 10):
        return [r for r in self.runs.values() if r.status == RunStatus.QUEUED][:limit]

    def mark_running(self, run: Run) -> Run:
        run.status = RunStatus.RUNNING
        self.runs[run.id] = run
        return run

    def mark_finished(self, run: Run) -> Run:
        run.status = RunStatus.FINISHED
        self.runs[run.id] = run
        return run

    def mark_failed(self, run: Run, error_message: str) -> Run:
        run.status = RunStatus.FAILED
        run.error_message = error_message
        self.runs[run.id] = run
        return run


class InMemoryEventSink(EventSink):
    def __init__(self):
        self.events = []

    def write_event(self, *, task_id: str, event_type: str, payload: dict) -> None:
        self.events.append((task_id, event_type, payload))


class SucceedingExecutor(RunExecutor):
    def __init__(self):
        self.executed = []

    def execute(self, run: Run) -> None:
        self.executed.append(run.id)


class FailingExecutor(RunExecutor):
    def execute(self, run: Run) -> None:
        raise RuntimeError("boom")


def test_process_single_run_success():
    run = Run(id="r1", task_id="t1", status=RunStatus.QUEUED)
    repo = InMemoryRunRepo([run])
    events = InMemoryEventSink()
    executor = SucceedingExecutor()

    process_single_run(repo=repo, events=events, executor=executor, run=run)

    assert repo.runs["r1"].status == RunStatus.FINISHED
    assert executor.executed == ["r1"]
    assert ("t1", "run_started", {"run_id": "r1"}) in events.events
    assert ("t1", "run_finished", {"run_id": "r1"}) in events.events


def test_process_single_run_failure():
    run = Run(id="r1", task_id="t1", status=RunStatus.QUEUED)
    repo = InMemoryRunRepo([run])
    events = InMemoryEventSink()
    executor = FailingExecutor()

    process_single_run(repo=repo, events=events, executor=executor, run=run)

    stored = repo.runs["r1"]
    assert stored.status == RunStatus.FAILED
    assert stored.error_message is not None
    # We still expect a "started" event before failure.
    assert any(e[1] == "run_started" for e in events.events)
    assert any(e[1] == "run_failed" for e in events.events)


def test_poll_once_processes_all_queued_runs():
    runs = [
        Run(id="r1", task_id="t1", status=RunStatus.QUEUED),
        Run(id="r2", task_id="t1", status=RunStatus.QUEUED),
    ]
    repo = InMemoryRunRepo(runs)
    events = InMemoryEventSink()
    executor = SucceedingExecutor()

    processed = poll_once(repo=repo, events=events, executor=executor, batch_size=10)

    assert processed == 2
    assert repo.runs["r1"].status == RunStatus.FINISHED
    assert repo.runs["r2"].status == RunStatus.FINISHED
    assert set(executor.executed) == {"r1", "r2"}


def test_poll_once_no_queued_runs_returns_zero():
    runs = [Run(id="r1", task_id="t1", status=RunStatus.FINISHED)]
    repo = InMemoryRunRepo(runs)
    events = InMemoryEventSink()
    executor = SucceedingExecutor()

    processed = poll_once(repo=repo, events=events, executor=executor, batch_size=10)

    assert processed == 0
    assert executor.executed == []
