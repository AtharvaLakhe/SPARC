"""ASGI middleware for a hard request-body byte limit, including chunked bodies."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import Request

from .errors import problem_response


Receive = Callable[[], Awaitable[dict[str, Any]]]
Send = Callable[[dict[str, Any]], Awaitable[None]]


class RequestBodyLimitMiddleware:
    def __init__(self, app, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: dict[str, Any], receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope.get("method") not in {"POST", "PUT", "PATCH"}:
            await self.app(scope, receive, send)
            return

        headers = {key.lower(): value for key, value in scope.get("headers", [])}
        content_length = headers.get(b"content-length")
        if content_length is not None:
            try:
                declared_size = int(content_length)
            except ValueError:
                await self._reject(scope, receive, send, 400, "INVALID_CONTENT_LENGTH", "Content-Length must be a non-negative integer.")
                return
            if declared_size < 0:
                await self._reject(scope, receive, send, 400, "INVALID_CONTENT_LENGTH", "Content-Length must be a non-negative integer.")
                return
            if declared_size > self.max_bytes:
                await self._too_large(scope, receive, send)
                return

        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            if message["type"] != "http.request":
                continue
            body.extend(message.get("body", b""))
            if len(body) > self.max_bytes:
                await self._too_large(scope, receive, send)
                return
            if not message.get("more_body", False):
                break

        replayed = False

        async def replay_receive() -> dict[str, Any]:
            nonlocal replayed
            if replayed:
                return {"type": "http.request", "body": b"", "more_body": False}
            replayed = True
            return {"type": "http.request", "body": bytes(body), "more_body": False}

        await self.app(scope, replay_receive, send)

    async def _too_large(self, scope: dict[str, Any], receive: Receive, send: Send) -> None:
        await self._reject(
            scope,
            receive,
            send,
            413,
            "REQUEST_TOO_LARGE",
            f"Request body exceeds the {self.max_bytes}-byte limit.",
        )

    @staticmethod
    async def _reject(
        scope: dict[str, Any],
        receive: Receive,
        send: Send,
        status: int,
        code: str,
        detail: str,
    ) -> None:
        response = problem_response(Request(scope), status, code, detail)
        await response(scope, receive, send)

