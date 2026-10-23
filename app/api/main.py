
import logging
import uuid
from app.api.auth_routes import auth_router
from fastapi import FastAPI, Request

from app.api.routes import router, health_router


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s:%(message)s",
)

app = FastAPI(
    title="GenAI RAG API",
    description="Production-style RAG API",
    version="1.0.0",
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
