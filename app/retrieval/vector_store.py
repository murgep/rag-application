import numpy as np

from app.models.schemas import DocumentChunk


class VectorStore:
    """
    Simple in-memory vector store.

    Stores document chunks and their embeddings,
    and supports cosine-similarity search.
    """

    def __init__(self):
        self.chunks: list[DocumentChunk] = []
        self.embeddings: list[list[float]] = []

    def add(
        self,
        chunks: list[DocumentChunk],
        embeddings: list[list[float]],
    ) -> None:
        """
        Add document chunks and their embeddings.
        """

        if len(chunks) != len(embeddings):
            raise ValueError(
                "Number of chunks must match "
                "number of embeddings."
            )

        self.chunks.extend(chunks)
        self.embeddings.extend(embeddings)

    @staticmethod
    def cosine_similarity(
        vector_a: list[float],
        vector_b: list[float],
    ) -> float:
        """
        Calculate cosine similarity between two vectors.
        """

        a = np.array(vector_a)
        b = np.array(vector_b)

        denominator = (
            np.linalg.norm(a) *
            np.linalg.norm(b)
        )

        if denominator == 0:
            return 0.0

        return float(
            np.dot(a, b) / denominator
        )

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 3,
    ) -> list[tuple[DocumentChunk, float]]:
        """
        Return the top-K most similar chunks.
        """

        if not self.chunks:
            return []

        results = []

        for chunk, embedding in zip(
            self.chunks,
            self.embeddings,
        ):
            similarity = self.cosine_similarity(
                query_embedding,
                embedding,
            )

            results.append(
                (chunk, similarity)
            )

        results.sort(
            key=lambda item: item[1],
            reverse=True,
        )

        return results[:top_k]