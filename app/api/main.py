from fastapi import FastAPI

from app.api.routes import router,APIRouter
from app.api.routes import router, health_router

app = FastAPI(
    title="GenAI RAG API",
    description="Production-style RAG API",
    version="1.0.0",
)


app.include_router(
    router,
    prefix="/api/v1",
)
app.include_router(health_router)
