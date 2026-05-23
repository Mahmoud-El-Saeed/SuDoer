from __future__ import annotations

from fastapi import FastAPI


def build_app() -> FastAPI:
    """Summarize daemon FastAPI app construction."""

    return FastAPI()


app = build_app()
