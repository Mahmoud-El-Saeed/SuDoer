from __future__ import annotations

from fastapi import FastAPI

from apps.daemon.api.ws import router as ws_router


def build_app() -> FastAPI:
    """Summarize daemon FastAPI app construction."""

    app = FastAPI()
    app.include_router(ws_router)
    return app


app = build_app()
