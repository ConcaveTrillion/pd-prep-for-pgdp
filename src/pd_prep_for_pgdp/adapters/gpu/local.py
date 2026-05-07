"""In-process "local" GPUBackend.

Currently a thin subclass of `CpuBackend`. The CPU pipeline already runs
the heavy bits — DocTR predictor + PyTorch — and those auto-select
`cuda:0` whenever `torch.cuda.is_available()` (see
`core.ocr._detect_torch_device`). So on a CUDA host, the same code path
serves both this `LocalBackend` and `CpuBackend` and the GPU is used
automatically.

Why subclass instead of alias? Two reasons:

1. The autodetect picks `local` when cupy + a working CUDA runtime are
   present (see `bootstrap._autodetect_gpu_backend`). Keeping a distinct
   class lets `app.state.gpu_backend.name == "local"` flow through to
   `/healthz` and logs so users can see the GPU branch was selected.
2. Roadmap §14 (P3): replace cv2/numpy primitives in Step 4 with
   `pd_book_tools.image_processing.cupy_processing` + nvImageCodec for
   source decode. That work overrides `process_page` here without
   touching `CpuBackend`.

History: prior to 2026-05-07 every method here raised
`NotImplementedError`, which crashed the app for any user whose
auto-detected backend was `local` — i.e. anyone with a working GPU.
Subclassing `CpuBackend` is the minimal fix.
"""

from __future__ import annotations

import logging
from typing import Any

from .cpu import CpuBackend

log = logging.getLogger(__name__)


def _torch_device_label() -> str:
    """Human-readable device the OCR predictor will use.

    Mirrors `core.ocr._detect_torch_device` but returns the richer
    "cuda:N" form when CUDA is the chosen device, so the startup log
    line ("local backend on cuda:0") tells the user which physical GPU
    they're using.
    """
    try:
        import torch  # type: ignore[import-not-found]

        if torch.cuda.is_available():
            try:
                return f"cuda:{torch.cuda.current_device()}"
            except Exception:
                return "cuda"
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
    except Exception:
        pass
    return "cpu"


class LocalBackend(CpuBackend):
    """In-process backend, picked when a CUDA host is autodetected.

    Inherits `process_page` / `run_ocr` / `run_batch` from `CpuBackend`.
    DocTR/PyTorch handle the CPU/CUDA branch internally — see
    `core.ocr._detect_torch_device`.
    """

    name = "local"  # type: ignore[assignment]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        log.info("local backend on %s", _torch_device_label())
