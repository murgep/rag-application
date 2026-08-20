from app.database.connection import get_connection
from app.models.schemas import DocumentChunk


class PostgreSQLVectorStore:
    """
    PostgreSQL + pgvector implementation of vector search.
    """

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 3,
    ) -> list[tuple[DocumentChunk, float]]:
        """
        Search PostgreSQL for the most similar chunks.

        Returns:
            List of (DocumentChunk, cosine_similarity)
        """

        if not query_embedding:
            return []

        if top_k <= 0:
            raise ValueError(
                "top_k must be greater than zero."
            )

        vector_string = (
            "["
            + ",".join(
                str(value)
                for value in query_embedding
            )
            + "]"
        )

        query = """
        SELECT
            chunk_id,
            document_id,
            text,
            page_number,
            source,
            extraction_method,
            1 - (embedding <=> %s::vector)
                AS similarity
        FROM chunks
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> %s::vector
        LIMIT %s;
        """

        connection = get_connection()

        try:
            with connection.cursor() as cursor:

                cursor.execute(
                    query,
                    (
                        vector_string,
                        vector_string,
                        top_k,
                    ),
                )

                rows = cursor.fetchall()

        finally:
            connection.close()

        results = []

        for row in rows:

            chunk = DocumentChunk(
                chunk_id=row[0],
                document_id=row[1],
                text=row[2],
                page_number=row[3],
                source=row[4],
                extraction_method=row[5],
            )

            similarity = float(row[6])

            results.append(
                (chunk, similarity)
            )

        return results