from __future__ import annotations

import time

from fastapi import FastAPI, Request
from fastapi.responses import Response
from loguru import logger

from finance_api.api.router import router
from finance_api.config import get_settings
from finance_api.observability import configure_logging


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings)
    app = FastAPI(title=settings.app_name, version="0.1.0")

    @app.on_event("startup")
    def log_startup() -> None:
        logger.info(
            "Starting {app_name} env={app_env} bind={host}:{port}",
            app_name=settings.app_name,
            app_env=settings.app_env,
            host=settings.api_host,
            port=settings.api_port,
        )

    @app.on_event("shutdown")
    def log_shutdown() -> None:
        logger.info("Shutting down {app_name}", app_name=settings.app_name)

    @app.middleware("http")
    async def log_requests(request: Request, call_next) -> Response:  # type: ignore[no-untyped-def]
        started_at = time.perf_counter()
        logger.info(
            "HTTP request started method={method} path={path}",
            method=request.method,
            path=request.url.path,
        )
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - started_at) * 1000
            logger.exception(
                "HTTP request failed method={method} path={path} duration_ms={duration_ms:.2f}",
                method=request.method,
                path=request.url.path,
                duration_ms=duration_ms,
            )
            raise

        duration_ms = (time.perf_counter() - started_at) * 1000
        logger.info(
            "HTTP request finished method={method} path={path} "
            "status={status} duration_ms={duration_ms:.2f}",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=duration_ms,
        )
        return response

    app.include_router(router)
    return app
