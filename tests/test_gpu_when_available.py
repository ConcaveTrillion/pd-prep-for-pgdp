"""GPU-conditional tests.

Skipped automatically on CPU-only hosts. On a CUDA host (cupy importable
+ runtime reachable) these exercise:
  - `_autodetect_gpu_backend()` returns 'local' (the CUDA branch),
  - `build_gpu_backend(Settings(gpu_backend='local'))` returns a LocalBackend,
  - `LocalBackend` is a real subclass of `CpuBackend` whose methods
    delegate (no `NotImplementedError`).

The `gpu_available` flag comes from the shared `tests/conftest.py`. When you
add a new test that needs CUDA, mark it with the same skipif and document
why it needs the GPU.
"""

from __future__ import annotations

import pytest

from pd_prep_for_pgdp.adapters.gpu.cpu import CpuBackend
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


def test_local_backend_subclasses_cpu_backend() -> None:
    """`LocalBackend` delegates the working pipeline to `CpuBackend`.

    Regression: prior to 2026-05-07 `LocalBackend.process_page` /
    `run_ocr` / `run_batch` were `NotImplementedError` stubs, so users
    on a CUDA host (auto-detected as `local`) saw the app crash on
    every page. Fix is `class LocalBackend(CpuBackend)` — DocTR/PyTorch
    pick up `cuda:0` automatically when available, so the same code
    path serves both CPU and GPU users. This test runs unconditionally
    (no `requires_gpu`) because the contract — "LocalBackend is not a
    stub" — is true on every host.
    """
    assert issubclass(LocalBackend, CpuBackend)
    # Methods must come from CpuBackend (or LocalBackend's own override),
    # never from the abstract base or a NotImplementedError stub.
    for method_name in ("process_page", "run_ocr", "run_batch"):
        method = getattr(LocalBackend, method_name)
        # Defined on CpuBackend (or overridden on LocalBackend) — not the Protocol.
        assert method is not None
        # Source code does not raise NotImplementedError.
        import inspect

        src = inspect.getsource(method)
        assert "NotImplementedError" not in src, (
            f"LocalBackend.{method_name} must not be a NotImplementedError stub"
        )


@pytest.mark.asyncio
@requires_gpu
async def test_local_backend_run_batch_delegates_on_gpu_host() -> None:
    """On a CUDA host, `LocalBackend.run_batch([])` returns `[]` instead
    of raising — proving the CpuBackend delegation reaches the live path."""
    backend = LocalBackend()
    result = await backend.run_batch([])
    assert result == []
