"""Lock in the per-region try/except in `_handle_extract_illustrations`.

A single bad region (e.g. coords clamping to an empty box) shouldn't
abort the rest of the page. The handler catches the per-region
exception, records it in `errors`, and continues to the next region.
"""

from __future__ import annotations

from datetime import UTC, datetime

import numpy as np
import pytest

from pd_prep_for_pgdp.adapters.database.sqlite import SqliteDatabase
from pd_prep_for_pgdp.adapters.storage.filesystem import FilesystemStorage
from pd_prep_for_pgdp.core.job_runner import (
    InProcessJobRunner,
    _handle_extract_illustrations,
)
from pd_prep_for_pgdp.core.models import (
    IllustrationRegion,
    Job,
    JobStatus,
    JobType,
    PageRecord,
    PipelineState,
    Project,
    ProjectConfig,
    ProjectStatus,
)


def _png(h: int, w: int) -> bytes:
    cv2 = pytest.importorskip("cv2")
    img = np.full((h, w, 3), 200, dtype=np.uint8)
    ok, buf = cv2.imencode(".png", img)
    assert ok
    return bytes(buf.tobytes())


@pytest.mark.asyncio
async def test_one_bad_region_doesnt_abort_the_rest(tmp_path) -> None:
    pytest.importorskip("cv2")
    db = SqliteDatabase(f"sqlite:///{(tmp_path / 's.db').as_posix()}")
    await db.initialize()
    storage = FilesystemStorage(root=tmp_path / "data")

    now = datetime.now(UTC)
    project = Project(
        id="il1",
        owner_id="default",
        name="t",
        created_at=now,
        updated_at=now,
        status=ProjectStatus.processing,
        page_count=1,
        proof_page_count=1,
        config=ProjectConfig(book_name="t", source_uri=""),
        pipeline_state=PipelineState(),
        storage_prefix="projects/il1/",
    )
    await db.put_project(project)

    src_key = "projects/il1/source/src1.png"
    await storage.put_bytes(src_key, _png(100, 100))

    page = PageRecord(
        project_id="il1",
        idx0=0,
        prefix="p001",
        source_stem="src1",
        source_key=src_key,
        illustration_regions=[
            # OK region: small valid crop.
            IllustrationRegion(index=1, L=10, R=50, T=10, B=50, output_format="jpg"),
            # BAD region: coords entirely outside 100x100 → ValueError in
            # extract_illustration → caught by handler's per-region try/except.
            IllustrationRegion(index=2, L=200, R=300, T=200, B=300, output_format="jpg"),
            # Another OK region after the bad one.
            IllustrationRegion(index=3, L=60, R=90, T=60, B=90, output_format="png"),
        ],
    )
    await db.put_pages([page])

    job = Job(
        id="j-mix",
        project_id="il1",
        owner_id="default",
        type=JobType.batch_extract_illustrations,
        status=JobStatus.queued,
    )
    await db.put_job(job)

    runner = InProcessJobRunner(database=db, storage=storage)
    await _handle_extract_illustrations(runner, job)

    # Two OK crops written to storage.
    assert await storage.exists("projects/il1/hi_res/p001_01.jpg")
    assert await storage.exists("projects/il1/hi_res/p001_03.png")
    # The bad region's output must NOT exist (it errored before writing).
    assert not await storage.exists("projects/il1/hi_res/p001_02.jpg")

    refreshed = await db.get_job("j-mix")
    assert refreshed is not None
    # Total counts the successful extractions; message reports errors.
    assert refreshed.progress.current == 2
    assert "1 errors" in refreshed.progress.message

    await db.close()
