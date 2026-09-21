import logging
import re
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.logging_config import configure_logging, request_id_var
from app.routers import auth, health, tasks

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger("app.request")

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Secure multi-user task management API (DevSecOps portfolio project).",
)

_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9-]{8,64}$")


@app.middleware("http")
async def request_context(request: Request, call_next):
    incoming = request.headers.get("X-Request-ID", "")
    # Only trust well-formed client IDs (prevents log injection).
    request_id = incoming if _REQUEST_ID_RE.match(incoming) else uuid.uuid4().hex
    token = request_id_var.set(request_id)
    start = time.perf_counter()
    try:
        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                "unhandled_exception",
                extra={"method": request.method, "path": request.url.path},
            )
            response = JSONResponse(
                status_code=500,
                content={"detail": "Internal server error", "request_id": request_id},
            )
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "request_completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round((time.perf_counter() - start) * 1000, 2),
            },
        )
        return response
    finally:
        request_id_var.reset(token)


app.include_router(health.router)
app.include_router(auth.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")
