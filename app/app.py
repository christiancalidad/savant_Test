import logging
import uuid
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.responses import Response
from starlette import status
from app.routers.voice import router as voice_router
from app.config import settings
from app.schemas import ErrorResponse

try:
    # Configure Azure Monitor for traces/logs/metrics when connection string is present
    from azure.monitor.opentelemetry import configure_azure_monitor  # type: ignore
except Exception:  # pragma: no cover - optional dependency at runtime
    configure_azure_monitor = None  # type: ignore

# Basic console logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
logger = logging.getLogger("app")

# Initialize Azure Monitor (Application Insights)
# In local/dev, suppress telemetry setup and quiet chatty SDK loggers so only app logs/prints show.
if settings.environment.lower() != "praoduction":
    # Do NOT configure Azure Monitor in local/dev even if connection string exists
    logger.info("Local/dev environment detected: telemetry disabled, showing only app logs/prints")
    # Quiet down telemetry/HTTP SDKs in local
    for noisy in (
        "azure",
        "azure.core",
        "azure.core.pipeline.policies.http_logging_policy",
        "azure.monitor",
        "azure.monitor.opentelemetry",
        "opentelemetry",
        "httpx",
        "urllib3",
    ):
        try:
            logging.getLogger(noisy).setLevel(logging.WARNING)
        except Exception:
            pass
else:
    # Production: configure Azure Monitor when available
    if settings.application_insights_connection_string and configure_azure_monitor:
        try:
            configure_azure_monitor(connection_string=settings.application_insights_connection_string)
            logger.info("Azure Monitor configured for Application Insights logging and tracing")
        except Exception as exc:  # don't block app startup on telemetry issues
            logger.warning(f"Failed to configure Azure Monitor: {exc}")
    else:
        logger.info("Azure Monitor not configured (no connection string or package not available)")

app = FastAPI(title=settings.app_name)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(voice_router)


# Lightweight request-id middleware for correlation
@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    request.state.request_id = request_id
    try:
        response: Response = await call_next(request)
    except Exception:
        # Ensure request-id is present even on unhandled exceptions
        response = JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=ErrorResponse(detail="Internal server error").model_dump())
    response.headers["x-request-id"] = request_id
    return response


# Global error handlers returning structured errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation error: {exc} | request_id={getattr(request.state, 'request_id', '-')}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(detail="Solicitud inválida: datos no válidos").model_dump(),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error: {exc} | request_id={getattr(request.state, 'request_id', '-')}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(detail="Error interno del servidor").model_dump(),
    )

# Serve simple frontend
app.mount("/frontend", StaticFiles(directory="app/frontend"), name="frontend")

@app.get("/")
def index():
    return FileResponse("app/frontend/index.html")
