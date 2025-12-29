from fastapi import APIRouter

from app.features.health.schemas import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Health check",
    description="Lightweight readiness endpoint.",
    response_description="Service health status.",
)
def health() -> HealthResponse:
    """Return service health status.

    Lightweight readiness endpoint for uptime checks.
    """
    return HealthResponse(status="ok")
