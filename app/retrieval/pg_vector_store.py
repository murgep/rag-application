
from app.database.connection import get_connection
from app.models.schemas import DocumentChunk


class PostgreSQLVectorStore:
    """PostgreSQL + pgvector implementation of vector search."""

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 3,
        department: str | None = None,
        departments: frozenset[str] | set[str] | None = None,
    ) -> list[tuple[DocumentChunk, float]]:
        """
        Search PostgreSQL for similar chunks.

        `department` preserves the legacy single-department interface.
        `departments` restricts results to an explicit allowlist.
        An empty allowlist returns no results.
        """

        if not query_embedding:
            return []

        if top_k <= 0:
            raise ValueError("top_k must be greater than zero.")

        # Do not permit callers to combine ambiguous filter modes.
        if departments is not None and department is not None:
            raise ValueError(
                "Provide either department or departments, not both."
            )

        if departments is not None:
            allowed_departments = sorted(set(departments))

            # Fail closed: an empty allowlist cannot search all departments.
            if not allowed_departments:
                return []

        elif department is not None:
            allowed_departments = [department]

        else:
            # Preserve legacy behavior for existing development/tests.
            # The authorization integration must never use this branch
            # for an authenticated user.
            allowed_departments = None

        vector_string = (
            "[" + ",".join(str(value) for value in query_embedding) + "]"
        )

        if allowed_departments is None:
            query = """
                SELECT
                    c.chunk_id,
                    c.document_id,
                    c.text,
                    c.page_number,
                    c.source,
                    c.extraction_method,
                    1 - (c.embedding <=> %s::vector) AS similarity
                FROM chunks c
                JOIN documents d
                    ON c.document_id = d.document_id
                WHERE c.embedding IS NOT NULL
                ORDER BY c.embedding <=> %s::vector
                LIMIT %s;
            """

            params = (
                vector_string,
                vector_string,
                top_k,
            )

        else:
            query = """
                SELECT
                    c.chunk_id,
                    c.document_id,
                    c.text,
                    c.page_number,
                    c.source,
                    c.extraction_method,
                    1 - (c.embedding <=> %s::vector) AS similarity
                FROM chunks c
                JOIN documents d
                    ON c.document_id = d.document_id
                WHERE c.embedding IS NOT NULL
                  AND d.department = ANY(%s)
                ORDER BY c.embedding <=> %s::vector
                LIMIT %s;
            """

            params = (
                vector_string,
                allowed_departments,
                vector_string,
                top_k,
            )

        connection = get_connection()

        try:
            with connection.cursor() as cursor:
                cursor.execute("SET LOCAL statement_timeout = '5s';")
                cursor.execute(query, params)
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
            results.append((chunk, float(row[6])))

        return results
