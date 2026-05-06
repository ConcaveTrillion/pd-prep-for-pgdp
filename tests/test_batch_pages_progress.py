"""Test that `_run_batch_pages` streams per-item progress through the JobEventBroker.

Locks in (P1#5 in docs/08-roadmap.md):
  - A 3-page batch produces at least 3 progress events while running, each
    with `total=3` and a monotonically increasing `current`.
  - `current_page` on each progress event matches the idx0 of the item that
    just settled, so the SPA can highlight the active row.
  - The final event from `_run_batch_pages` itself summarises ok/err.
  - Errors don't abort the batch — a mid-batch failure still yields a
    progress event for the failed item; subsequent items run normally.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import pytest

from pd_prep_for_pgdp.adapters.database.sqlite import SqliteDatabase
from pd_prep_for_pgdp.adapters.gpu.base import (
    BatchJobItem,
    BatchJobResult,
    BatchProgressCb,
    OcrPageRequest,
    OcrPageResponse,
    ProcessPageRequest,
    ProcessPageResponse,
)
from pd_prep_for_pgdp.adapters.storage.filesystem import FilesystemStorage
from pd_prep_for_pgdp.core.job_events import JobEventBroker
from pd_prep_for_pgdp.core.job_runner import InProcessJobRunner, _run_batch_pages
from pd_prep_for_pgdp.core.models import (
    Job,
    JobStatus,
    JobType,
    PageRecord,
    PipelineState,
    Project,
    ProjectConfig,
    ProjectStatus,
)


class _FakeBackend:
    """Minimal GPUBackend stand-in for batch progress tests.

    `process_page` and `run_ocr` are unused on this code path; only
    `run_batch` is exercised. Each item is acknowledged synchronously
    (with optional per-idx0 failures) and `progress_cb` is invoked after
    every item — the same contract `CpuBackend.run_batch` honours.
    """

    name = "cpu"

    def __init__(self, *, fail_idxs: set[int] | None = None) -> None:
        self._fail_idxs = fail_idxs or set()

    async def process_page(self, req: ProcessPageRequest) -> ProcessPageResponse:  # pragma: no cover
        raise AssertionError("not used by _run_batch_pages")

    async def run_ocr(self, req: OcrPageRequest) -> OcrPageResponse:  # pragma: no cover
        raise AssertionError("not used by _run_batch_pages")

    async def run_batch(
        self,
        items: list[BatchJobItem],
        *,
        progress_cb: BatchProgressCb | None = None,
    ) -> list[BatchJobResult]:
        results: list[BatchJobResult] = []
        total = len(items)
        for item in items:
            if item.idx0 in self._fail_idxs:
                result = BatchJobResult(
                    job_type=item.job_type,
                    project_id=item.project_id,
                    idx0=item.idx0,
                    ok=False,
                    error=f"forced failure for idx0={item.idx0}",
                )
            else:
                result = BatchJobResult(
                    job_type=item.job_type,
                    project_id=item.project_id,
                    idx0=item.idx0,
                    ok=True,
                )
            results.append(result)
            if progress_cb is not None:
                await progress_cb(len(results), total, result)
        return results


@pytest.fixture
async def db(tmp_path) -> SqliteDatabase:
    d = SqliteDatabase(f"sqlite:///{(tmp_path / 's.db').as_posix()}")
    await d.initialize()
    return d


@pytest.fixture
def storage(tmp_path) -> FilesystemStorage:
    return FilesystemStorage(root=tmp_path / "data")


def _project(project_id: str = "p1") -> Project:
    now = datetime.now(UTC)
    return Project(
        id=project_id,
        owner_id="default",
        name="t",
        created_at=now,
        updated_at=now,
        status=ProjectStatus.processing,
        page_count=3,
        proof_page_count=3,
        config=ProjectConfig(book_name="t", source_uri=""),
        pipeline_state=PipelineState(),
        storage_prefix=f"projects/{project_id}/",
    )


def _page(project_id: str, idx0: int) -> PageRecord:
    return PageRecord(
        project_id=project_id,
        idx0=idx0,
        prefix=f"p{idx0 + 1:03d}",
        source_stem=f"src{idx0}",
    )


@pytest.mark.asyncio
async def test_batch_pages_streams_per_item_progress_events(
    db: SqliteDatabase, storage: FilesystemStorage
) -> None:
    """3-page batch → at least 3 progress events with monotonic `current` and
    matching `current_page`."""
    project = _project()
    await db.put_project(project)
    await db.put_pages([_page(project.id, i) for i in range(3)])

    events = JobEventBroker()
    runner = InProcessJobRunner(
        database=db,
        storage=storage,
        gpu=_FakeBackend(),
        events=events,
    )

    job = Job(
        id="bp-3",
        project_id=project.id,
        owner_id="default",
        type=JobType.batch_process_pages,
        status=JobStatus.running,  # mimic `_run_one` having flipped it already
    )
    await db.put_job(job)

    received: list[dict] = []

    async def listen() -> None:
        async for ev in events.subscribe("bp-3"):
            received.append(ev)

    listener = asyncio.create_task(listen())
    await asyncio.sleep(0.01)

    await _run_batch_pages(runner, job, job_type="batch_process_pages")
    # Close the channel so the listener returns; production does this from
    # `_emit` on terminal status, but this test calls `_run_batch_pages`
    # directly without the surrounding `_run_one` wrapper.
    await events.close("bp-3")
    await asyncio.wait_for(listener, timeout=2.0)

    progress = [e for e in received if e["type"] == "progress"]
    per_item = [e for e in progress if e.get("total") == 3]
    assert len(per_item) >= 3, f"expected >=3 per-item progress events; got {received}"

    currents = [e["current"] for e in per_item]
    assert currents == sorted(currents), f"non-monotonic: {currents}"
    assert max(currents) == 3

    # The first three per-item events should report current_page == idx0 (0,1,2).
    item_events = per_item[:3]
    assert [e["current_page"] for e in item_events] == [0, 1, 2]


@pytest.mark.asyncio
async def test_batch_pages_progress_continues_through_per_item_errors(
    db: SqliteDatabase, storage: FilesystemStorage
) -> None:
    """A failure on idx0=1 doesn't suppress the progress event for that item or abort the batch."""
    project = _project()
    await db.put_project(project)
    await db.put_pages([_page(project.id, i) for i in range(3)])

    events = JobEventBroker()
    runner = InProcessJobRunner(
        database=db,
        storage=storage,
        gpu=_FakeBackend(fail_idxs={1}),
        events=events,
    )

    job = Job(
        id="bp-err",
        project_id=project.id,
        owner_id="default",
        type=JobType.batch_process_pages,
        status=JobStatus.running,
    )
    await db.put_job(job)

    received: list[dict] = []

    async def listen() -> None:
        async for ev in events.subscribe("bp-err"):
            received.append(ev)

    listener = asyncio.create_task(listen())
    await asyncio.sleep(0.01)

    await _run_batch_pages(runner, job, job_type="batch_process_pages")
    await events.close("bp-err")
    await asyncio.wait_for(listener, timeout=2.0)

    per_item = [e for e in received if e["type"] == "progress" and e.get("total") == 3]
    # All three pages reported.
    assert {e["current_page"] for e in per_item[:3]} == {0, 1, 2}
    # The running ok/err message reflects the mix at every step (ok=2 err=1 by the end).
    final_running = per_item[2]["message"]
    assert "ok=2" in final_running and "err=1" in final_running
