"""RFC 9457-style responses that never expose internal exception details."""

from __future__ import annotations

from http import HTTPStatus
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class SparcError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        detail: str,
        *,
        invalid_params: list[dict[str, str]] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(code)
        self.status_code = status_code
        self.code = code
        self.detail = detail
        self.invalid_params = invalid_params or []
        self.headers = headers or {}


def problem_response(
    request: Request,
    status_code: int,
    code: str,
    detail: str,
    *,
    invalid_params: list[dict[str, str]] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    try:
        title = HTTPStatus(status_code).phrase
    except ValueError:
        title = "Error"
    trace_id = getattr(request.state, "request_id", "req:unavailable")
    body = {
        "type": f"https://sparc.example/problems/{code.lower().replace('_', '-')}",
        "title": title[:200],
        "status": status_code,
        "detail": detail[:500],
        "instance": request.url.path[:400],
        "code": code[:80],
        "traceId": trace_id,
        "invalidParams": (invalid_params or [])[:20],
    }
    response_headers = {"Cache-Control": "no-store", **(headers or {})}
    return JSONResponse(
        body,
        status_code=status_code,
        media_type="application/problem+json",
        headers=response_headers,
    )


async def sparc_error_handler(request: Request, exc: SparcError) -> JSONResponse:
    return problem_response(
        request,
        exc.status_code,
        exc.code,
        exc.detail,
        invalid_params=exc.invalid_params,
        headers=exc.headers,
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    invalid_params: list[dict[str, str]] = []
    for error in exc.errors()[:20]:
        location = [str(part) for part in error.get("loc", ()) if part not in {"body", "path", "query"}]
        name = ".".join(location) or "request"
        invalid_params.append(
            {
                "name": name[:128],
                "reason": str(error.get("msg", "invalid value"))[:300],
            }
        )
    return problem_response(
        request,
        422,
        "VALIDATION_ERROR",
        "The request contains invalid or unsupported values.",
        invalid_params=invalid_params,
    )


async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    safe_messages = {
        404: "The requested resource was not found.",
        405: "The HTTP method is not supported for this resource.",
    }
    return problem_response(
        request,
        exc.status_code,
        f"HTTP_{exc.status_code}",
        safe_messages.get(exc.status_code, "The request could not be completed."),
        headers=exc.headers,
    )


async def internal_error_handler(request: Request, _exc: Exception) -> JSONResponse:
    return problem_response(
        request,
        500,
        "INTERNAL_ERROR",
        "The service could not complete the request.",
    )
