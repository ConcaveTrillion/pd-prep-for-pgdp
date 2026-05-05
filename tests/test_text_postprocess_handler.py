"""Edge cases for `_handle_text_postprocess`.

Locks in:
  - Pages flagged `ignore=True` are skipped (text NOT rewritten),
  - Pages whose recorded `output.ocr_text_key` doesn't exist on storage
    are skipped (no crash),
  - The progress.message reports the count of files actually rewritten.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from pd_prep_for_pgdp.adapters.database.sqlite import SqliteDatabase
from pd_prep_for_pgdp.adapters.storage.filesystem import FilesystemStorage
from pd_prep_for_pgdp.core.job_runner import InProcessJobRunner, _handle_text_postprocess
from pd_prep_for_pgdp.core.models import (
    Job,
    JobStatus,
    JobType,
    PageOutput,
    PageRecord,
    PipelineState,
    Project,
    ProjectConfig,
    ProjectStatus,
)


@pytest.fixture
async def db(tmp_path) -> SqliteDatabase:
    d = SqliteDatabase(f"sqlite:///{(tmp_path / 's.db').as_posix()}")
    await d.initialize()
    return d


@pytest.fixture
def storage(tmp_path) -> FilesystemStorage:
    return FilesystemStorage(root=tmp_path / "data")


def _project() -> Project:
    now = datetime.now(UTC)
    return Project(
        id="tp1",
        owner_id="default",
        name="t",
        created_at=now,
        updated_at=now,
        status=ProjectStatus.processing,
        page_count=2,
        proof_page_count=2,
        config=ProjectConfig(book_name="t", source_uri=""),
        pipeline_state=PipelineState(),
        storage_prefix="projects/tp1/",
    )


@pytest.mark.asyncio
async def test_text_postprocess_skips_ignored_pages(db, storage) -> None:
    """A page marked ignore=True must NOT have its text touched."""
    await db.put_project(_project())
    text_key_ok = "projects/tp1/ocr_text/src1_p001.txt"
    text_key_skip = "projects/tp1/ocr_text/src2_p002.txt"
    await storage.put_bytes(text_key_ok, b"He said \xe2\x80\x9chi\xe2\x80\x9d.")
    await storage.put_bytes(text_key_skip, b"He said \xe2\x80\x9cBYE\xe2\x80\x9d.")

    pages = [
        PageRecord(
            project_id="tp1",
            idx0=0,
            prefix="p001",
            source_stem="src1",
            outputs=[
                PageOutput(
                    full_prefix="p001",
                    split_suffix=None,
                    reading_order=0,
                    ocr_text_key=text_key_ok,
                )
            ],
        ),
        PageRecord(
            project_id="tp1",
            idx0=1,
            prefix="p002",
            source_stem="src2",
            ignore=True,  # skip
            outputs=[
                PageOutput(
                    full_prefix="p002",
                    split_suffix=None,
                    reading_order=0,
                    ocr_text_key=text_key_skip,
                )
            ],
        ),
    ]
    await db.put_pages(pages)
    job = Job(
        id="j",
        project_id="tp1",
        owner_id="default",
        type=JobType.batch_text_postprocess,
        status=JobStatus.queued,
    )
    await db.put_job(job)

    runner = InProcessJobRunner(database=db, storage=storage)
    await _handle_text_postprocess(runner, job)

    # Page 0 was rewritten (curly quotes → straight).
    after_ok = (await storage.get_bytes(text_key_ok)).decode()
    assert '"hi"' in after_ok
    # Page 1 (ignored) was NOT touched — still has curly quotes.
    after_skip = (await storage.get_bytes(text_key_skip)).decode()
    assert "“" in after_skip  # left-double-quotation-mark, untouched

    # Progress reports 1 file processed.
    refreshed = await db.get_job("j")
    assert refreshed is not None
    assert "1" in refreshed.progress.message


@pytest.mark.asyncio
async def test_text_postprocess_skips_missing_files_silently(db, storage) -> None:
    """A recorded ocr_text_key that doesn't exist on storage is just skipped —
    no exception, no crash, no error event."""
    await db.put_project(_project())
    page = PageRecord(
        project_id="tp1",
        idx0=0,
        prefix="p001",
        source_stem="src1",
        outputs=[
            PageOutput(
                full_prefix="p001",
                split_suffix=None,
                reading_order=0,
                ocr_text_key="projects/tp1/ocr_text/never_written.txt",
            )
        ],
    )
    await db.put_pages([page])
    job = Job(
        id="j-m",
        project_id="tp1",
        owner_id="default",
        type=JobType.batch_text_postprocess,
        status=JobStatus.queued,
    )
    await db.put_job(job)

    runner = InProcessJobRunner(database=db, storage=storage)
    await _handle_text_postprocess(runner, job)

    refreshed = await db.get_job("j-m")
    assert refreshed is not None
    # Zero files processed; progress reports it cleanly.
    assert "0" in refreshed.progress.message
