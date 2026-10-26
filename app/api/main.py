import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.auth_routes import auth_router
from app.api.routes import router, health_router

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s:%(message)s",
)

app = FastAPI(
    title="GenAI RAG API",
    description="Production-style RAG API",
    version="1.0.0",
)

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "unknown")

    logger.error(
        "Unhandled request exception; request_id=%s",
        request_id,
        exc_info=(type(exc), exc, exc.__traceback__),
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An internal error occurred while processing the request.",
            }
        },
        headers={"X-Request-ID": request_id},
    )

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

app.include_router(auth_router, prefix="/api/v1")
app.include_router(router, prefix="/api/v1")
app.include_router(health_router)
