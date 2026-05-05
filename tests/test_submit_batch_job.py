"""Tests for `POST /api/gpu/jobs` (submit_batch_job).

Locks in:
  - submitting a batch_process_pages job creates a queued/scheduled job,
  - `page_idxs` is recorded into the job's payload (so the runner can
    process only the requested pages),
  - estimated_pages reflects the requested count,
  - 404 for an unknown / other-user project,
  - 404 for an unknown project_id (vs. payload-validation 422).
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from pd_prep_for_pgdp.adapters.database.sqlite import SqliteDatabase
from pd_prep_for_pgdp.bootstrap import build_app
from pd_prep_for_pgdp.core.models import (
    PipelineState,
    Project,
    ProjectConfig,
    ProjectStatus,
)
from pd_prep_for_pgdp.settings import Settings


def _settings(tmp_path) -> Settings:
    return Settings(
        host="127.0.0.1",
        port=8765,
        data_root=tmp_path / "data",
        config_dir=tmp_path / "config",
        storage_backend="filesystem",
        database_url=f"sqlite:///{(tmp_path / 's.db').as_posix()}",
        gpu_backend="cpu",
        dispatch_interval_seconds=0,
        auth_mode="none",
    )


def _seed(settings: Settings, owner_id: str = "default") -> None:
    async def go() -> None:
        db = SqliteDatabase(settings.derived_database_url)
        await db.initialize()
        now = datetime.now(UTC)
        await db.put_project(
            Project(
                id="bj1",
                owner_id=owner_id,
                name="t",
                created_at=now,
                updated_at=now,
                status=ProjectStatus.processing,
                page_count=5,
                proof_page_count=5,
                config=ProjectConfig(book_name="t", source_uri=""),
                pipeline_state=PipelineState(),
                storage_prefix="projects/bj1/",
            )
        )
        await db.close()

    asyncio.run(go())


def test_submit_creates_queued_job(tmp_path) -> None:
    settings = _settings(tmp_path)
    _seed(settings)
    app = build_app(settings)
    with TestClient(app) as client:
        r = client.post(
            "/api/gpu/jobs",
            json={"project_id": "bj1", "job_type": "batch_process_pages"},
        )
        assert r.status_code == 202, r.text
        body = r.json()
        assert body["status"] in ("queued", "scheduled")
        assert body["estimated_pages"] == 0
        assert body["dispatch_mode"] == "immediate"

        # Job actually exists.
        job = client.get(f"/api/data/jobs/{body['job_id']}").json()
        assert job["type"] == "batch_process_pages"
        assert job["payload"] == {}


def test_submit_records_page_idxs_in_payload(tmp_path) -> None:
    settings = _settings(tmp_path)
    _seed(settings)
    app = build_app(settings)
    with TestClient(app) as client:
        r = client.post(
            "/api/gpu/jobs",
            json={
                "project_id": "bj1",
                "job_type": "batch_ocr",
                "page_idxs": [0, 2, 4],
            },
        )
        assert r.status_code == 202
        body = r.json()
        assert body["estimated_pages"] == 3

        job = client.get(f"/api/data/jobs/{body['job_id']}").json()
        assert job["payload"] == {"page_idxs": [0, 2, 4]}


def test_submit_unknown_project_404(tmp_path) -> None:
    settings = _settings(tmp_path)
    app = build_app(settings)
    with TestClient(app) as client:
        r = client.post(
            "/api/gpu/jobs",
            json={"project_id": "no-such", "job_type": "batch_process_pages"},
        )
        assert r.status_code == 404


def test_submit_other_users_project_404(tmp_path) -> None:
    settings = _settings(tmp_path)
    _seed(settings, owner_id="someone-else")
    app = build_app(settings)
    with TestClient(app) as client:
        r = client.post(
            "/api/gpu/jobs",
            json={"project_id": "bj1", "job_type": "batch_process_pages"},
        )
        assert r.status_code == 404
