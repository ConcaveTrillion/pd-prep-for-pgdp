"""Shared-GPU-container GPUBackend — HTTP client to a long-running ECS task.

Used in managed mode when a tenant has enough sustained GPU traffic to
amortise an always-on EC2 GPU instance.
"""

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


class SharedContainerBackend(GPUBackend):
    name = "shared_container"

    def __init__(self, base_url: str, api_key: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key

    async def process_page(self, req: ProcessPageRequest) -> ProcessPageResponse:
        # Issues HTTP POST to {base_url}/api/gpu/process-page with bearer token.
        # Wired in a later iteration once httpx flow is set up.
        raise NotImplementedError("shared_container.process_page not yet wired")

    async def run_ocr(self, req: OcrPageRequest) -> OcrPageResponse:
        raise NotImplementedError("shared_container.run_ocr not yet wired")

    async def run_batch(
        self,
        items: list[BatchJobItem],
        *,
        progress_cb: BatchProgressCb | None = None,
    ) -> list[BatchJobResult]:
        # `progress_cb` is part of the Protocol; the HTTP path will hook into
        # SSE / chunked-transfer events once the route + client are wired.
        raise NotImplementedError("shared_container.run_batch not yet wired")
