"""Tests for the synchronous-dispatch routes:

  - POST /api/gpu/process-page → forwards to gpu.process_page()
  - POST /api/gpu/run-ocr-page  → forwards to gpu.run_ocr()

Both routes are thin wrappers — we just need to confirm the request
body is decoded into the right pydantic model and the backend's
response is returned verbatim. We override `get_gpu_backend` via
FastAPI's dependency_overrides to inject a fake backend.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from pd_prep_for_pgdp.adapters.gpu.base import (
    GPUBackend,
    OcrPageRequest,
    OcrPageResponse,
    ProcessPageRequest,
    ProcessPageResponse,
)
from pd_prep_for_pgdp.api.dependencies import get_gpu_backend
from pd_prep_for_pgdp.bootstrap import build_app
from pd_prep_for_pgdp.settings import Settings


class _FakeBackend(GPUBackend):
    name = "fake"

    def __init__(self) -> None:
        self.process_calls: list[ProcessPageRequest] = []
        self.ocr_calls: list[OcrPageRequest] = []

    async def process_page(self, req: ProcessPageRequest) -> ProcessPageResponse:
        self.process_calls.append(req)
        return ProcessPageResponse(
            processed_image_key=f"projects/{req.project_id}/processed/idx_{req.idx0}.png",
            processed_image_url="/cdn/processed",
            dimensions=(1000, 600),
            processing_time_ms=42,
            backend="cpu",
            cold_start_ms=0,
        )

    async def run_ocr(self, req: OcrPageRequest) -> OcrPageResponse:
        self.ocr_calls.append(req)
        return OcrPageResponse(
            text="hello world",
            words=[],
            text_key=f"projects/{req.project_id}/ocr_text/idx_{req.idx0}.txt",
        )

    async def run_batch(self, items):  # pragma: no cover - unused
        return []


def _client(settings: Settings) -> tuple[TestClient, _FakeBackend]:
    app = build_app(settings)
    fake = _FakeBackend()
    app.dependency_overrides[get_gpu_backend] = lambda: fake
    return TestClient(app), fake


def test_process_page_route_forwards_request_and_returns_response(settings: Settings) -> None:
    client, fake = _client(settings)
    with client:
        r = client.post(
            "/api/gpu/process-page",
            json={
                "project_id": "p1",
                "idx0": 7,
                "config_overrides": {},
                "output_context": "workbench",
            },
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["processed_image_key"] == "projects/p1/processed/idx_7.png"
        assert body["dimensions"] == [1000, 600]
        assert body["backend"] == "cpu"

    # Backend got the decoded request.
    assert len(fake.process_calls) == 1
    assert fake.process_calls[0].project_id == "p1"
    assert fake.process_calls[0].idx0 == 7


def test_run_ocr_page_route_forwards_request_and_returns_response(settings: Settings) -> None:
    client, fake = _client(settings)
    with client:
        r = client.post(
            "/api/gpu/run-ocr-page",
            json={"project_id": "p1", "idx0": 3},
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["text"] == "hello world"
        assert body["text_key"] == "projects/p1/ocr_text/idx_3.txt"

    assert len(fake.ocr_calls) == 1
    assert fake.ocr_calls[0].idx0 == 3
