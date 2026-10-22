
from typing import Protocol

from app.embeddings.embedder import Embedder
from app.models.schemas import DocumentChunk


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

        query_embedding = self.embedder.embed_text(query)

        if departments is not None:
            return self.vector_store.search(
                query_embedding=query_embedding,
                top_k=top_k,
                departments=departments,
            )

        return self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            department=department,
        )
