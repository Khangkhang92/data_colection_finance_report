from __future__ import annotations

import sys
import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import Response
from loguru import logger

_HERE = Path(__file__).resolve()
_PROJECT_ROOT = _HERE.parents[2]
_FINANCE_API_SRC = _PROJECT_ROOT / "app" / "services" / "finance_report"
_FINANCE_RAG_SRC = _PROJECT_ROOT / "app" / "services" / "finance_rag_service"
_FINANCE_RAG_LOGIC = _FINANCE_RAG_SRC / "business_logic"
_COMMON_SERVICE_ROOT = _PROJECT_ROOT / "app" / "common"
for path in (str(_FINANCE_API_SRC), str(_FINANCE_RAG_SRC), str(_FINANCE_RAG_LOGIC), str(_COMMON_SERVICE_ROOT)):
    if path not in sys.path:
        sys.path.append(path)

from api.router import router
from common.config.finance_api import get_settings
from common.logging.finance_api import configure_logging

settings = get_settings()
configure_logging(settings)
app = FastAPI(title="finance-gateway-api", version="0.1.0")


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
    logger.info("HTTP request started method={method} path={path}", method=request.method, path=request.url.path)
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
        "HTTP request finished method={method} path={path} status={status} duration_ms={duration_ms:.2f}",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration_ms=duration_ms,
    )
    return response


app.include_router(router)
