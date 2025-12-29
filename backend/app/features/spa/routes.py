from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse


def create_spa_router(frontend_dist: Path) -> APIRouter:
    """Build a router that serves the SPA index for unknown paths.

    Non-API routes fall back to index.html to support client routing.
    """
    router = APIRouter()

    @router.get(
        "/{full_path:path}",
        response_class=FileResponse,
        tags=["SPA"],
        summary="SPA fallback",
        description="Serves index.html for unknown client routes.",
        response_description="SPA index file.",
        responses={
            200: {"content": {"text/html": {}}},
            404: {"description": "Not found."},
        },
    )
    def spa_fallback(full_path: str) -> FileResponse:
        """Serve the SPA index.html for unknown client routes.

        API, asset, health, and file extension paths return 404.
        """
        if (
            full_path.startswith("api/")
            or full_path.startswith("assets/")
            or full_path == "health"
            or "." in full_path
        ):
            raise HTTPException(status_code=404, detail="Not Found")
        return FileResponse(frontend_dist / "index.html")

    return router
