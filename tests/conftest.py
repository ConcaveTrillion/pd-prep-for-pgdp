"""Shared pytest fixtures.

`temp_settings` builds a Settings instance pointing at an isolated tmpdir so
every test gets a clean filesystem-storage / SQLite database / no-auth setup.

`gpu_available` is True when cupy is importable AND a working CUDA runtime
is reachable. Tests that exercise the real LocalBackend path use
`@pytest.mark.skipif(not gpu_available, reason=...)` so they run on
CUDA hosts (incl. this devcontainer when present) and skip cleanly on
CPU-only CI.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from pd_prep_for_pgdp.bootstrap import build_app
from pd_prep_for_pgdp.settings import Settings


def _detect_gpu() -> bool:
    """True iff cupy can import AND `cupy.cuda.is_available()` succeeds.

    Both checks are needed — cupy can install without a working CUDA runtime
    (e.g. wheel mismatch) and the import succeeds but device queries fail.
    """
    try:
        import cupy  # type: ignore[import-not-found]
    except ImportError:
        return False
    try:
        return bool(cupy.cuda.is_available())
    except Exception:
        return False


gpu_available: bool = _detect_gpu()


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        host="127.0.0.1",
        port=8765,
        data_root=tmp_path / "data",
        config_dir=tmp_path / "config",
        storage_backend="filesystem",
        database_url=f"sqlite:///{(tmp_path / 'state.db').as_posix()}",
        auth_mode="none",
        gpu_backend="cpu",
        dispatch_interval_seconds=0,
    )


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    app = build_app(settings)
    with TestClient(app) as c:
        yield c
