from typing import Protocol

from app.embeddings.embedder import Embedder
from app.models.schemas import DocumentChunk


class SearchableVectorStore(Protocol):
    """
    Interface required by the Retriever.
    """

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 3,
    ) -> list[tuple[DocumentChunk, float]]:
        ...


class Retriever:
    """
    Converts a user query into relevant document chunks.
    """

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
    ) -> list[tuple[DocumentChunk, float]]:
        """
        Generate a query embedding and retrieve
        the most relevant document chunks.
        """

        if not query.strip():
            raise ValueError(
                "Query cannot be empty."
            )

        query_embedding = self.embedder.embed_text(
            query
        )

        return self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
        )






#################### Below code is we made for testing privious concept##################

# from app.embeddings.embedder import Embedder
# from app.models.schemas import DocumentChunk
# from app.retrieval.vector_store import VectorStore
#
#
# class Retriever:
#     """
#     Responsible for converting a user query into
#     relevant document chunks.
#     """
#
#     def __init__(
#         self,
#         embedder: Embedder,
#         vector_store: VectorStore,
#     ):
#         self.embedder = embedder
#         self.vector_store = vector_store
#
#     def retrieve(
#         self,
#         query: str,
#         top_k: int = 3,
#     ) -> list[tuple[DocumentChunk, float]]:
#         """
#         Retrieve the most relevant chunks for a query.
#         """
#
#         if not query.strip():
#             raise ValueError(
#                 "Query cannot be empty."
#             )
#
#         query_embedding = self.embedder.embed_text(
#             query
#         )
#
#         return self.vector_store.search(
#             query_embedding=query_embedding,
#             top_k=top_k,
#         )