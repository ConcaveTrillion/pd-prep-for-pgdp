"""Lock in the local-mode batch error path in `_run_batch_pages`.

When the runner runs items inline (no BatchDispatcher) and any items fail,
the runner records `error_message = first_err` on the job so the user
sees the cause in the JobsPage.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from pd_prep_for_pgdp.adapters.database.sqlite import SqliteDatabase
from pd_prep_for_pgdp.adapters.gpu.base import BatchJobItem, BatchJobResult, GPUBackend
from pd_prep_for_pgdp.adapters.storage.filesystem import FilesystemStorage
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


class _MixedBackend(GPUBackend):
    """Returns ok for idx0=0, error for idx0=1."""

    name = "mixed"

    async def process_page(self, req):  # pragma: no cover - unused
        raise NotImplementedError

    async def run_ocr(self, req):  # pragma: no cover - unused
        raise NotImplementedError

    async def run_batch(
        self,
        items: list[BatchJobItem],
        *,
        progress_cb=None,
    ) -> list[BatchJobResult]:
        out: list[BatchJobResult] = []
        for item in items:
            if item.idx0 == 0:
                out.append(
                    BatchJobResult(
                        job_type=item.job_type,
                        project_id=item.project_id,
                        idx0=item.idx0,
                        ok=True,
                    )
                )
            else:
                out.append(
                    BatchJobResult(
                        job_type=item.job_type,
                        project_id=item.project_id,
                        idx0=item.idx0,
                        ok=False,
                        error="page failed: synthetic boom",
                    )
                )
        return out


@pytest.fixture
async def db(tmp_path) -> SqliteDatabase:
    d = SqliteDatabase(f"sqlite:///{(tmp_path / 's.db').as_posix()}")
    await d.initialize()
    return d


@pytest.fixture
def storage(tmp_path) -> FilesystemStorage:
    return FilesystemStorage(root=tmp_path / "data")


@pytest.mark.asyncio
async def test_local_batch_records_first_error_on_job(db, storage) -> None:
    runner = InProcessJobRunner(database=db, storage=storage, gpu=_MixedBackend())
    now = datetime.now(UTC)
    await db.put_project(
        Project(
            id="lb1",
            owner_id="default",
            name="t",
            created_at=now,
            updated_at=now,
            status=ProjectStatus.processing,
            page_count=2,
            proof_page_count=2,
            config=ProjectConfig(book_name="t", source_uri=""),
            pipeline_state=PipelineState(),
            storage_prefix="projects/lb1/",
        )
    )
    await db.put_pages(
        [
            PageRecord(project_id="lb1", idx0=0, prefix="p001", source_stem="s1"),
            PageRecord(project_id="lb1", idx0=1, prefix="p002", source_stem="s2"),
        ]
    )
    job = Job(
        id="j-mix",
        project_id="lb1",
        owner_id="default",
        type=JobType.batch_process_pages,
        status=JobStatus.queued,
    )
    await db.put_job(job)

    await _run_batch_pages(runner, job, job_type="batch_process_pages")

    refreshed = await db.get_job("j-mix")
    assert refreshed is not None
    assert refreshed.error_message
    assert "synthetic boom" in refreshed.error_message
    # Both the error_message AND the progress count must survive — the
    # error-persist path uses the up-to-date `latest` job reference.
    assert "ok=1 err=1" in refreshed.progress.message
