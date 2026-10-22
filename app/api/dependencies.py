
from fastapi import HTTPException, status

from app.auth.authorization import UserPermissions
from app.embeddings.embedder import Embedder
from app.generation.generator import Generator
from app.rag.pipeline import RAGPipeline
from app.retrieval.pg_vector_store import PostgreSQLVectorStore
from app.retrieval.retriever import Retriever


def get_rag_pipeline() -> RAGPipeline:
    """Build the RAG pipeline and its dependencies."""

    embedder = Embedder()
    vector_store = PostgreSQLVectorStore()

    retriever = Retriever(
        embedder=embedder,
        vector_store=vector_store,
    )

    generator = Generator()

    return RAGPipeline(
        retriever=retriever,
        generator=generator,
    )


def get_current_user_permissions() -> UserPermissions:
    """
    Authentication is not configured yet.

    Deny API access until this dependency is replaced with one
    that derives identity from a verified authentication token.
    Tests may override this dependency with test permissions.
    """

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "code": "AUTHENTICATION_REQUIRED",
            "message": "A verified user identity is required.",
        },
        headers={"WWW-Authenticate": "Bearer"},
    )
