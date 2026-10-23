
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.authorization import (
    AuthorizationError,
    AuthorizationService,
    UserPermissions,
)
from app.auth.tokens import TokenError, verify_access_token
from app.embeddings.embedder import Embedder
from app.generation.generator import Generator
from app.rag.pipeline import RAGPipeline
from app.retrieval.pg_vector_store import PostgreSQLVectorStore
from app.retrieval.retriever import Retriever


bearer_scheme = HTTPBearer(auto_error=False)


def get_rag_pipeline() -> RAGPipeline:
    """Build the RAG pipeline and its dependencies."""
    embedder = Embedder()
    vector_store = PostgreSQLVectorStore()
    retriever = Retriever(embedder=embedder, vector_store=vector_store)
    generator = Generator()
    return RAGPipeline(retriever=retriever, generator=generator)


def get_current_user_permissions(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> UserPermissions:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "AUTHENTICATION_REQUIRED",
                "message": "A valid Bearer token is required.",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = verify_access_token(credentials.credentials)
        return AuthorizationService().get_user_permissions(user_id)
    except TokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_TOKEN",
                "message": "The access token is invalid or expired.",
            },
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    except AuthorizationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_USER",
                "message": "The user is unavailable or inactive.",
            },
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
