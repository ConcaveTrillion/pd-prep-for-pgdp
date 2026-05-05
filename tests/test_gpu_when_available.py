"""GPU-conditional tests.

Skipped automatically on CPU-only hosts. On a CUDA host (cupy importable
+ runtime reachable) these exercise:
  - `_autodetect_gpu_backend()` returns 'local' (the CUDA branch),
  - `build_gpu_backend(Settings(gpu_backend='local'))` returns a LocalBackend,
  - LocalBackend's NotImplementedError contract is preserved (so this test
    surfaces if someone wires up the GPU pipeline without updating the test
    suite).

The `gpu_available` flag comes from the shared `tests/conftest.py`. When you
add a new test that needs CUDA, mark it with the same skipif and document
why it needs the GPU.
"""

from __future__ import annotations

import pytest

from pd_prep_for_pgdp.adapters.gpu.local import LocalBackend
from pd_prep_for_pgdp.bootstrap import _autodetect_gpu_backend, build_gpu_backend
from pd_prep_for_pgdp.settings import Settings

from .conftest import gpu_available

requires_gpu = pytest.mark.skipif(not gpu_available, reason="requires a working CUDA runtime + cupy")


@requires_gpu
def test_autodetect_picks_local_when_cuda_available() -> None:
    """On a CUDA host, autodetect should pick 'local' (the GPU backend).

    This is the production-relevant complement to the CPU-fallback test in
    test_bootstrap_builders.py: there we mock cupy out; here we exercise the
    real import.
    """
    assert _autodetect_gpu_backend() == "local"


@requires_gpu
def test_build_gpu_backend_returns_local_for_explicit_setting(tmp_path) -> None:
    """`gpu_backend='local'` in Settings yields a LocalBackend instance."""
    settings = Settings(
        host="127.0.0.1",
        port=8765,
        data_root=tmp_path / "data",
        config_dir=tmp_path / "config",
        storage_backend="filesystem",
        database_url=f"sqlite:///{(tmp_path / 's.db').as_posix()}",
        gpu_backend="local",
        dispatch_interval_seconds=0,
        auth_mode="none",
    )
    backend = build_gpu_backend(settings)
    assert isinstance(backend, LocalBackend)
    assert backend.name == "local"


@pytest.mark.asyncio
@requires_gpu
async def test_local_backend_methods_are_not_yet_wired() -> None:
    """LocalBackend's process_page / run_ocr / run_batch all raise
    NotImplementedError today (per CLAUDE.md). When that changes, this
    test should be replaced with a real GPU smoke test exercising the
    new pipeline. Until then, this lock prevents accidental partial wiring."""
    from pd_prep_for_pgdp.adapters.gpu.base import (
        OcrPageRequest,
        ProcessPageRequest,
    )
    from pd_prep_for_pgdp.core.models import PageConfigOverrides

    backend = LocalBackend()

    with pytest.raises(NotImplementedError):
        await backend.process_page(
            ProcessPageRequest(
                project_id="p",
                idx0=0,
                config_overrides=PageConfigOverrides(),
                output_context="commit",
            )
        )

    with pytest.raises(NotImplementedError):
        await backend.run_ocr(OcrPageRequest(project_id="p", idx0=0))

    with pytest.raises(NotImplementedError):
        await backend.run_batch([])
