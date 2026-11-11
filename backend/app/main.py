"""MaddyView — FastAPI application entry point."""

import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import auth, deposits, finance, goals, system
from app.core.config import get_settings
from app.core.errors import register_error_handlers
from app.core.logging import configure_logging, get_logger, request_id_var

settings = get_settings()
configure_logging(settings.log_level)
log = get_logger("finpilot.http")

UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def create_app() -> FastAPI:
    app = FastAPI(
        title="MaddyView API",
        version="0.1.0",
        description="Personal financial intelligence platform — Milestone 1 foundation. "
        "No real-money trading or automatic transactions are supported.",
        docs_url=f"{settings.api_v1_prefix}/docs",
        redoc_url=f"{settings.api_v1_prefix}/redoc",
        openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    )

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        rid = request.headers.get("x-request-id") or uuid.uuid4().hex[:16]
        token = request_id_var.set(rid)
        start = time.perf_counter()
        try:
            # CSRF defence in depth (cookie is also SameSite=Lax): browsers always send Origin on
            # cross-origin unsafe requests, so reject any Origin we have not allow-listed.
            origin = request.headers.get("origin")
            if request.method in UNSAFE_METHODS and origin and origin not in settings.cors_origins:
                response = JSONResponse(status_code=403, content={"error": {
                    "code": "forbidden_origin", "message": "Origin not allowed", "details": None, "request_id": rid}})
            else:
                response = await call_next(request)
            response.headers["x-request-id"] = rid
            response.headers["x-content-type-options"] = "nosniff"
            response.headers["x-frame-options"] = "DENY"
            response.headers["referrer-policy"] = "no-referrer"
            response.headers["cache-control"] = response.headers.get("cache-control", "no-store")
            log.info("request", extra={"method": request.method, "path": request.url.path,
                                       "status": response.status_code,
                                       "ms": round((time.perf_counter() - start) * 1000, 1)})
            return response
        finally:
            request_id_var.reset(token)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["content-type", "x-request-id"],
    )
    register_error_handlers(app)

    prefix = settings.api_v1_prefix
    for module in (system, auth, finance, deposits, goals):
        app.include_router(module.router, prefix=prefix)
    return app


app = create_app()
