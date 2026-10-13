import logging
from collections.abc import Awaitable, Callable
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response

from app.core.config import get_settings
from app.modules.service_status.api.router import router as public_router
from app.modules.technical_record.api.router import router

logger = logging.getLogger(__name__)
app = FastAPI(
    title="Proyecto Arquitectura — HU-06 + HU-07",
    description=(
        "Expediente técnico interno y consulta pública de estado de servicio."
    ),
    version="0.1.0",
)
app.include_router(router)
app.include_router(public_router)


@app.middleware("http")
async def disable_api_caching(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    response = await call_next(request)
    if request.url.path.startswith("/api/v1/"):
        response.headers["Cache-Control"] = "no-store"
    return response


@app.exception_handler(Exception)
async def internal_error_handler(_request: Request, _error: Exception) -> JSONResponse:
    logger.exception("Error interno procesando una solicitud")
    return JSONResponse(
        status_code=500,
        content={
            "type": "about:blank",
            "title": "Error interno",
            "status": 500,
            "detail": "No fue posible procesar la solicitud. Intente nuevamente.",
        },
        headers={"Cache-Control": "no-store"},
    )


frontend_directory = Path(get_settings().frontend_dir)
app.mount("/", StaticFiles(directory=frontend_directory, html=True), name="frontend")
