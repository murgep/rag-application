import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from app.api.dependencies import get_rag_pipeline
from app.database.connection import get_connection
from app.rag.pipeline import RAGPipeline


logger = logging.getLogger(__name__)

router = APIRouter()
health_router = APIRouter()


# ============================================================
# Request / Response Models
# ============================================================

class AskRequest(BaseModel):
    question: str = Field(min_length=1)

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Question cannot be empty or whitespace")
        return value


class SourceResponse(BaseModel):
    document_id: str
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
        "Submit a question to the RAG pipeline and receive "
        "an answer with source information."
    ),
    responses={
        500: {
            "model": ErrorEnvelope,
            "description": "Internal server error",
        }
    },
)
def ask_question(
    request: AskRequest,
    rag: RAGPipeline = Depends(get_rag_pipeline),
):
    try:
        response = rag.ask(
            question=request.question,
        )

        return response



    except Exception:

        logger.exception("RAG request failed")

        return JSONResponse(

            status_code=500,

            content={

                "error": {

                    "code": "INTERNAL_ERROR",

                    "message": "An internal error occurred while processing the request.",

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
    return {
        "status": "healthy"
    }


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

        return {
            "status": "ready"
        }


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

################################# This was to check fast api is working or not##################

# from fastapi import APIRouter
# from pydantic import BaseModel
#
#
# router = APIRouter()
#
#
# class AskRequest(BaseModel):
#     question: str
#
#
# @router.post("/ask")
# def ask_question(request: AskRequest):
#     return {
#         "message": "RAG endpoint is working",
#         "question": request.question,
#     }