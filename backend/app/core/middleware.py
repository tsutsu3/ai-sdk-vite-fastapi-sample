from collections.abc import Iterable

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.core.request_id import generate_request_id, reset_request_id, set_request_id
from app.features.authz.request_context import (
    reset_request_context,
    resolve_request_context,
    set_request_context,
)


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Attach a request id to every incoming request.

    The request id is used to correlate logs and error responses
    across services and async operations.
    """

    def __init__(self, app, *, header_name: str = "x-request-id") -> None:
        super().__init__(app)
        self._header_name = header_name

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        request_id = request.headers.get(self._header_name) or generate_request_id()
        token = set_request_id(request, request_id)
        try:
            response = await call_next(request)
        finally:
            reset_request_id(token)
        response.headers[self._header_name] = request_id
        return response


class AuthzContextMiddleware(BaseHTTPMiddleware):
    """Populate authz request context via middleware.

    The authz context is resolved once per request so handlers can rely on
    tenant/user information without repeating authorization lookups.
    """

    def __init__(
        self,
        app,
        *,
        exclude_paths: Iterable[str] | None = None,
        exclude_prefixes: Iterable[str] | None = None,
    ) -> None:
        super().__init__(app)
        self._exclude_paths = set(exclude_paths or [])
        self._exclude_prefixes = tuple(exclude_prefixes or ())

    def _should_apply(self, request: Request) -> bool:
        if request.method == "OPTIONS":
            return False
        path = request.url.path
        if not path.startswith("/api"):
            return False
        if path in self._exclude_paths:
            return False
        if any(path.startswith(prefix) for prefix in self._exclude_prefixes):
            return False
        return True

    @staticmethod
    def _error_response(request: Request, exc: HTTPException) -> JSONResponse:
        trace_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "message": exc.detail,
                    "type": "http_error",
                    "code": str(exc.status_code),
                },
                "detail": exc.detail,
                "trace_id": trace_id,
            },
        )

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        if not self._should_apply(request):
            return await call_next(request)

        try:
            context = await resolve_request_context(request)
        except HTTPException as exc:
            return self._error_response(request, exc)

        tokens = set_request_context(request, context)
        try:
            return await call_next(request)
        finally:
            reset_request_context(tokens)
