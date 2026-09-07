import logging
import time
from http import HTTPStatus
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

_STATUS_CODES = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    409: "conflict",
    413: "payload_too_large",
    415: "unsupported_media_type",
    422: "validation_error",
    429: "rate_limit_exceeded",
}


def global_error_handler(app: FastAPI) -> None:
    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        request.state.request_id = str(uuid4())
        started = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - started) * 1000
        response.headers["X-Request-ID"] = request.state.request_id
        response.headers["Server-Timing"] = f"app;dur={duration_ms:.2f}"
        if duration_ms >= 250:
            logger.warning(
                "Slow API request method=%s path=%s status=%s duration_ms=%.2f request_id=%s",
                request.method,
                request.url.path,
                response.status_code,
                duration_ms,
                request.state.request_id,
            )
        return response

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(
        request: Request, error: StarletteHTTPException
    ) -> JSONResponse:
        if isinstance(error.detail, dict):
            code = str(error.detail.get("code") or _code_for_status(error.status_code))
            message = str(
                error.detail.get("message") or _message_for_status(error.status_code)
            )
            details = error.detail.get("details")
        else:
            code = _code_for_status(error.status_code)
            message = str(error.detail or _message_for_status(error.status_code))
            details = None

        return _response(
            request,
            status_code=error.status_code,
            code=code,
            message=message,
            details=details,
            headers=error.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, error: RequestValidationError
    ) -> JSONResponse:
        details = [
            {
                "field": ".".join(str(part) for part in issue["loc"]),
                "message": issue["msg"],
                "type": issue["type"],
            }
            for issue in error.errors()
        ]
        return _response(
            request,
            status_code=422,
            code="validation_error",
            message="The request contains invalid or missing fields",
            details=details,
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(
        request: Request, error: Exception
    ) -> JSONResponse:
        request_id = _request_id(request)
        logger.exception(
            "Unhandled API error request_id=%s", request_id, exc_info=error
        )
        return _response(
            request,
            status_code=500,
            code="internal_server_error",
            message="An unexpected error occurred",
        )


def _response(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
    details: object | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    request_id = _request_id(request)
    error: dict[str, object] = {
        "code": code,
        "message": message,
        "request_id": request_id,
    }
    if details is not None:
        error["details"] = details

    response_headers = dict(headers or {})
    response_headers["X-Request-ID"] = request_id
    return JSONResponse(
        status_code=status_code,
        content={"error": error},
        headers=response_headers,
    )


def _request_id(request: Request) -> str:
    request_id = getattr(request.state, "request_id", None)
    if request_id is None:
        request_id = str(uuid4())
        request.state.request_id = request_id
    return request_id


def _code_for_status(status_code: int) -> str:
    return _STATUS_CODES.get(status_code, f"http_{status_code}_error")


def _message_for_status(status_code: int) -> str:
    try:
        return HTTPStatus(status_code).phrase
    except ValueError:
        return "Request failed"
