import logging
import time
from typing import Protocol

from app.embeddings.embedder import Embedder
from app.models.schemas import DocumentChunk


logger = logging.getLogger(__name__)


class SearchableVectorStore(Protocol):
    """Interface required by the Retriever."""

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 3,
        department: str | None = None,
        departments: frozenset[str] | set[str] | None = None,
    ) -> list[tuple[DocumentChunk, float]]:
        ...


class Retriever:
    """Converts a user query into relevant document chunks."""

    def __init__(
        self,
        embedder: Embedder,
        vector_store: SearchableVectorStore,
    ):
        self.embedder = embedder
        self.vector_store = vector_store

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        department: str | None = None,
        departments: frozenset[str] | set[str] | None = None,
    ) -> list[tuple[DocumentChunk, float]]:
        """Embed a query and retrieve matching document chunks."""

        if not query.strip():
            raise ValueError("Query cannot be empty.")

        if department is not None and departments is not None:
            raise ValueError(
                "Provide either department or departments, not both."
            )

        # Measure query embedding latency.
        embedding_start = time.perf_counter()
        query_embedding = self.embedder.embed_text(query)
        embedding_duration = time.perf_counter() - embedding_start

        logger.info(
            "Query embedding completed; duration=%.3f seconds",
            embedding_duration,
        )

        # Measure vector-store search latency.
        search_start = time.perf_counter()

        if departments is not None:
            results = self.vector_store.search(
                query_embedding=query_embedding,
                top_k=top_k,
                departments=departments,
            )
        else:
            results = self.vector_store.search(
                query_embedding=query_embedding,
                top_k=top_k,
                department=department,
            )

        search_duration = time.perf_counter() - search_start

        logger.info(
            "Vector search completed; duration=%.3f seconds results=%d",
            search_duration,
            len(results),
        )

        return results