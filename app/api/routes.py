
import logging
import time

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.api.dependencies import (
    get_current_user_permissions,
    get_rag_pipeline,
)
from app.auth.authorization import UserPermissions
from app.database.connection import get_connection
from app.rag.pipeline import RAGPipeline


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

router = APIRouter()
health_router = APIRouter()


# ============================================================
# Request / Response Models
# ============================================================

class AskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1, max_length=2000)

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Question cannot be empty or whitespace.")
        return value


class SourceResponse(BaseModel):
    document_id: str
    source: str
    page_number: int
    similarity: float


class QuestionResponse(BaseModel):
    answer: str
    sources: list[SourceResponse]


class ErrorResponse(BaseModel):
    code: str
    message: str


class ErrorEnvelope(BaseModel):
    error: ErrorResponse


# ============================================================
# RAG API
# ============================================================

@router.post(
    "/ask",
    response_model=QuestionResponse,
    summary="Ask a question",
    description=(
        "Submit a question to the RAG pipeline. Retrieval is limited "
        "to the authenticated user's explicitly authorized departments."
    ),
    responses={
        401: {
            "model": ErrorEnvelope,
            "description": "Authentication required",
        },
        403: {
            "model": ErrorEnvelope,
            "description": "No authorized department access",
        },
        500: {
            "model": ErrorEnvelope,
            "description": "Internal server error",
        },
    },
)
def ask_question(
    request: Request,
    payload: AskRequest,
    permissions: UserPermissions = Depends(get_current_user_permissions),
    rag: RAGPipeline = Depends(get_rag_pipeline),
):
    request_id = getattr(request.state, "request_id", "test-request")
    start_time = time.perf_counter()

    # Fail closed: no department assignment means no retrieval.
    if not permissions.departments:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "DEPARTMENT_ACCESS_DENIED",
                "message": "You are not authorized to access any department.",
            },
        )

    try:
        response = rag.ask(
            question=payload.question,
            departments=permissions.departments,
            request_id=request_id,
        )

        logger.info(
            "RAG request completed; user_id=%s request_id=%s "
            "duration=%.3f seconds",
            permissions.user_id,
            request_id,
            time.perf_counter() - start_time,
        )

        return response

    except Exception:
        logger.exception(
            "RAG request failed; user_id=%s request_id=%s duration=%.3f seconds",
            permissions.user_id,
            request_id,
            time.perf_counter() - start_time,
        )

        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": (
                        "An internal error occurred while processing the request."
                    ),
                }
            },
        )


# ============================================================
# Health / Readiness
# ============================================================

@health_router.get(
    "/health",
    summary="Health check",
    description="Check whether the API service is running.",
)
def health_check():
    return {"status": "healthy"}


@health_router.get(
    "/readiness",
    summary="Readiness check",
    description="Check whether the API can connect to PostgreSQL.",
    responses={
        503: {
            "model": ErrorEnvelope,
            "description": "Service is not ready",
        }
    },
)
def readiness_check():
    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")

        return {"status": "ready"}

    except Exception:
        logger.exception("Readiness check failed")

        return JSONResponse(
            status_code=503,
            content={
                "error": {
                    "code": "SERVICE_NOT_READY",
                    "message": "Service is not ready.",
                }
            },
        )
