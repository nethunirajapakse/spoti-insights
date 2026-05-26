import time
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable

logger = logging.getLogger("api.requests")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # SAFEGUARD: If Redis is down, SlowAPI might fail to attach 'view_rate_limit'.
        # We ensure it exists here so subsequent code doesn't crash.
        if not hasattr(request.state, "view_rate_limit"):
            request.state.view_rate_limit = None

        request_id = request.headers.get("X-Request-ID", str(time.time()))
        logger.info(f"[{request_id}] {request.method} {request.url.path}")

        start_time = time.time()

        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            logger.info(
                f"[{request_id}] Status: {response.status_code} "
                f"Duration: {process_time:.3f}s"
            )

            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)
            return response

        except Exception as e:
            # logger.exception captures the full stack trace, not just the message.
            logger.exception(f"[{request_id}] Request failed with error: {str(e)}")
            raise
