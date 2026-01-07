import time
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import json

logger = logging.getLogger("api.requests")

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID", str(time.time()))
        
        logger.info(f"[{request_id}] {request.method} {request.url.path}")
        
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    logger.debug(f"[{request_id}] Request body: {body.decode()}")
            except Exception:
                pass
        
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        logger.info(
            f"[{request_id}] Status: {response.status_code} "
            f"Duration: {process_time:.3f}s"
        )
        
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
