"""Lock in `CpuBackend._load_context` and `_empty_overrides` helpers.

`_load_context` is the read-context helper used by both `process_page`
and `run_ocr` (and indirectly by `run_batch`). Locks in:
  - missing project raises FileNotFoundError mentioning the id,
  - missing page raises FileNotFoundError mentioning the page coordinate,
  - happy path returns (project, system, page).

`_empty_overrides` is a tiny factory — locks in that it returns a
default PageConfigOverrides instance so the dispatcher path in
`run_batch` never crashes when the caller didn't pass overrides.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from pd_prep_for_pgdp.adapters.database.sqlite import SqliteDatabase
from pd_prep_for_pgdp.adapters.gpu.cpu import CpuBackend, _empty_overrides
from pd_prep_for_pgdp.adapters.storage.filesystem import FilesystemStorage
from pd_prep_for_pgdp.core.models import (
    PageConfigOverrides,
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


@pytest.mark.asyncio
async def test_load_context_missing_project_raises(db, storage) -> None:
    backend = CpuBackend(storage=storage, database=db)
    with pytest.raises(FileNotFoundError, match="project not found: ghost"):
        await backend._load_context("ghost", 0)


@pytest.mark.asyncio
async def test_load_context_missing_page_raises(db, storage) -> None:
    now = datetime.now(UTC)
    await db.put_project(
        Project(
            id="lc1",
            owner_id="default",
            name="t",
            created_at=now,
            updated_at=now,
            status=ProjectStatus.processing,
            page_count=0,
            proof_page_count=0,
            config=ProjectConfig(book_name="t", source_uri=""),
            pipeline_state=PipelineState(),
            storage_prefix="projects/lc1/",
        )
    )
    backend = CpuBackend(storage=storage, database=db)
    with pytest.raises(FileNotFoundError, match=r"page not found: lc1/0"):
        await backend._load_context("lc1", 0)


@pytest.mark.asyncio
async def test_load_context_happy_path_returns_tuple(db, storage) -> None:
    now = datetime.now(UTC)
    project = Project(
        id="lc2",
        owner_id="default",
        name="t",
        created_at=now,
        updated_at=now,
        status=ProjectStatus.processing,
        page_count=1,
        proof_page_count=1,
        config=ProjectConfig(book_name="t", source_uri=""),
        pipeline_state=PipelineState(),
        storage_prefix="projects/lc2/",
    )
    await db.put_project(project)
    page = PageRecord(project_id="lc2", idx0=0, prefix="p001", source_stem="src1")
    await db.put_pages([page])

    backend = CpuBackend(storage=storage, database=db)
    p, system, pg = await backend._load_context("lc2", 0)
    assert p.id == "lc2"
    assert pg.idx0 == 0
    assert system is not None  # default SystemDefaults instance


def test_empty_overrides_returns_default_pageconfigoverrides() -> None:
    o = _empty_overrides()
    assert isinstance(o, PageConfigOverrides)
    # All fields default to None — every override field is opt-in.
    assert o.threshold_level is None
    assert o.initial_crop is None
