from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse


def create_spa_router(frontend_dist: Path) -> APIRouter:
    router = APIRouter()

    @router.get("/{full_path:path}", response_class=FileResponse)
    def spa_fallback(full_path: str) -> FileResponse:
        if (
            full_path.startswith("api/")
            or full_path.startswith("assets/")
            or full_path == "health"
            or "." in full_path
        ):
            raise HTTPException(status_code=404, detail="Not Found")
        return FileResponse(frontend_dist / "index.html")

    return router
