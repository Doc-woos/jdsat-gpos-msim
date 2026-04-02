"""FastAPI application for standalone MSim."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.api.routes import router


WEB_DIR = Path(__file__).resolve().parent.parent / "web"
STATIC_DIR = WEB_DIR / "static"
INDEX_FILE = WEB_DIR / "index.html"


def create_app() -> FastAPI:
    """Create the MSim FastAPI application."""
    app = FastAPI(
        title="MSim",
        version="0.1.0",
        description="Standalone MSim force analytics backend",
    )
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    app.include_router(router, prefix="/api")

    @app.get("/")
    async def analyst_workbench() -> FileResponse:
        """Serve the minimal analyst workbench."""
        return FileResponse(INDEX_FILE)

    return app


app = create_app()
