"""In-process CUDA GPUBackend (CuPy + GPU PyTorch / DocTR)."""

from __future__ import annotations

from .base import (
    BatchJobItem,
    BatchJobResult,
    BatchProgressCb,
    GPUBackend,
    OcrPageRequest,
    OcrPageResponse,
    ProcessPageRequest,
    ProcessPageResponse,
)


class LocalBackend(GPUBackend):
    name = "local"

    async def process_page(self, req: ProcessPageRequest) -> ProcessPageResponse:
        raise NotImplementedError("core.pipeline.process_page not yet wired")

    async def run_ocr(self, req: OcrPageRequest) -> OcrPageResponse:
        raise NotImplementedError("core.ocr.run_ocr not yet wired")

    async def run_batch(
        self,
        items: list[BatchJobItem],
        *,
        progress_cb: BatchProgressCb | None = None,
    ) -> list[BatchJobResult]:
        # `progress_cb` is part of the Protocol; the CUDA path will wire
        # per-item streaming once `process_page_cuda` lands.
        raise NotImplementedError("core.pipeline.run_batch not yet wired")
