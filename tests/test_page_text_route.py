"""Tests for the page-text routes:

  - PATCH /projects/{id}/pages/{idx0}/text  — write text bytes,
  - GET   /projects/{id}/pages/{idx0}/text/{suffix} — read back.

Locks in:
  - PATCH writes a UTF-8 file under the synthesised key when no recorded
    `output.ocr_text_key` exists yet,
  - GET 404s for missing project / missing page / missing file,
  - GET 404 for another user's project (no-leak),
  - the `_` suffix in the URL maps to "" (whole-page) per spec.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from pd_prep_for_pgdp.adapters.database.sqlite import SqliteDatabase
from pd_prep_for_pgdp.bootstrap import build_app
from pd_prep_for_pgdp.core.models import (
    PageRecord,
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
                id="pt1",
                owner_id=owner_id,
                name="t",
                created_at=now,
                updated_at=now,
                status=ProjectStatus.processing,
                page_count=1,
                proof_page_count=1,
                config=ProjectConfig(book_name="t", source_uri=""),
                pipeline_state=PipelineState(),
                storage_prefix="projects/pt1/",
            )
        )
        await db.put_pages(
            [
                PageRecord(
                    project_id="pt1",
                    idx0=0,
                    prefix="p001",
                    source_stem="src1",
                )
            ]
        )
        await db.close()

    asyncio.run(go())


def test_patch_text_writes_synthesised_key_for_pre_ocr_page(tmp_path) -> None:
    """No `output.ocr_text_key` is recorded yet → handler synthesises the
    `projects/<id>/ocr_text/<stem>_<prefix>.txt` path and writes there."""
    settings = _settings(tmp_path)
    _seed(settings)
    app = build_app(settings)
    with TestClient(app) as client:
        r = client.patch(
            "/api/data/projects/pt1/pages/0/text",
            json={"text": "edited content", "split_suffix": ""},
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["text_key"].endswith("/ocr_text/src1_p001.txt")

        # GET it back via the read route — `_` decodes to "" (whole-page).
        r2 = client.get("/api/data/projects/pt1/pages/0/text/_")
        assert r2.status_code == 200
        assert r2.json()["text"] == "edited content"


def test_get_text_404_when_file_missing(tmp_path) -> None:
    settings = _settings(tmp_path)
    _seed(settings)
    app = build_app(settings)
    with TestClient(app) as client:
        # Page exists, but no file written yet.
        r = client.get("/api/data/projects/pt1/pages/0/text/_")
        assert r.status_code == 404


def test_get_text_404_for_unknown_project(tmp_path) -> None:
    settings = _settings(tmp_path)
    app = build_app(settings)
    with TestClient(app) as client:
        r = client.get("/api/data/projects/no-such/pages/0/text/_")
        assert r.status_code == 404


def test_get_text_404_for_unknown_page(tmp_path) -> None:
    settings = _settings(tmp_path)
    _seed(settings)
    app = build_app(settings)
    with TestClient(app) as client:
        r = client.get("/api/data/projects/pt1/pages/99/text/_")
        assert r.status_code == 404


def test_get_text_404_for_other_users_project(tmp_path) -> None:
    settings = _settings(tmp_path)
    _seed(settings, owner_id="someone-else")
    app = build_app(settings)
    with TestClient(app) as client:
        r = client.get("/api/data/projects/pt1/pages/0/text/_")
        assert r.status_code == 404


def test_patch_text_404_for_unknown_project(tmp_path) -> None:
    settings = _settings(tmp_path)
    app = build_app(settings)
    with TestClient(app) as client:
        r = client.patch(
            "/api/data/projects/no-such/pages/0/text",
            json={"text": "x", "split_suffix": ""},
        )
        assert r.status_code == 404


def test_patch_text_404_for_unknown_page(tmp_path) -> None:
    settings = _settings(tmp_path)
    _seed(settings)
    app = build_app(settings)
    with TestClient(app) as client:
        r = client.patch(
            "/api/data/projects/pt1/pages/99/text",
            json={"text": "x", "split_suffix": ""},
        )
        assert r.status_code == 404
