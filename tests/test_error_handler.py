"""Lock in the uniform error envelope from `api.middleware.error_handler`.

Locks in:
  - HTTPException → `{error: "http_<code>", message, details: null}`,
  - RequestValidationError → 400 `{error: "validation_error", details: [...]}`,
  - Any other unhandled exception → 500 `{error: "internal_error", ...}`
    with the traceback tail in `details`. We trigger this by mounting a
    one-off route that raises RuntimeError.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from pd_prep_for_pgdp.api.middleware.error_handler import install_error_handlers


def _app_with_routes() -> FastAPI:
    app = FastAPI()
    install_error_handlers(app)

    @app.get("/boom")
    async def boom() -> dict:
        raise RuntimeError("synthetic crash")

    @app.get("/teapot")
    async def teapot() -> dict:
        from fastapi import HTTPException

        raise HTTPException(status_code=418, detail="i am a teapot")

    @app.post("/echo")
    async def echo(payload: dict) -> dict:
        return payload

    return app


def test_http_exception_uses_envelope() -> None:
    with TestClient(_app_with_routes()) as client:
        r = client.get("/teapot")
        assert r.status_code == 418
        body = r.json()
        assert body["error"] == "http_418"
        assert body["message"] == "i am a teapot"
        assert body["details"] is None


def test_unhandled_exception_returns_500_envelope() -> None:
    """A bare RuntimeError leaks through; the catch-all handler converts
    it into a 500 with `error="internal_error"` and the last 3 traceback
    lines in `details`."""
    with TestClient(_app_with_routes(), raise_server_exceptions=False) as client:
        r = client.get("/boom")
        assert r.status_code == 500
        body = r.json()
        assert body["error"] == "internal_error"
        assert "synthetic crash" in body["message"]
        # Traceback tail is captured in details.
        assert isinstance(body["details"], list)
        assert any("synthetic crash" in line for line in body["details"])


def test_validation_error_returns_400_envelope() -> None:
    """Sending non-JSON to a route expecting a JSON body trips
    RequestValidationError, which the handler maps to 400."""
    with TestClient(_app_with_routes()) as client:
        r = client.post("/echo", content=b"not json", headers={"content-type": "application/json"})
        assert r.status_code == 400
        body = r.json()
        assert body["error"] == "validation_error"
        assert isinstance(body["details"], list)
