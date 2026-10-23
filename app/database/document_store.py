from app.database.connection import get_connection
from app.models.schemas import DocumentChunk


class DocumentStore:
    """
    Handles persistence of documents and chunks
    in PostgreSQL.
    """

    
    def save_document(
        self,
        document_id: str,
        filename: str,
        file_type: str,
        source: str,
        department: str | None = None,
        status: str = "active",
        effective_date=None,
    ) -> None:
        if status not in {"active", "inactive"}:
            raise ValueError("status must be 'active' or 'inactive'.")

        query = """
            INSERT INTO documents (
                document_id,
                filename,
                file_type,
                source,
                department,
                status,
                effective_date
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (document_id)
            DO UPDATE SET
                filename = EXCLUDED.filename,
                file_type = EXCLUDED.file_type,
                source = EXCLUDED.source,
                department = EXCLUDED.department,
                status = EXCLUDED.status,
                effective_date = EXCLUDED.effective_date;
        """

        connection = get_connection()

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    query,
                    (
                        document_id,
                        filename,
                        file_type,
                        source,
                        department,
                        status,
                        effective_date,
                    ),
                )

            connection.commit()

        finally:
            connection.close()

    def save_chunks(
        self,
        chunks: list[DocumentChunk],
        embeddings: list[list[float]],
    ) -> None:
        """
        Insert document chunks and their embeddings.
        """

        if len(chunks) != len(embeddings):
            raise ValueError(
                "Number of chunks must match "
                "number of embeddings."
            )

        query = """
        INSERT INTO chunks (
            chunk_id,
            document_id,
            text,
            page_number,
            source,
            extraction_method,
            embedding
        )
        VALUES (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s::vector
        )
        ON CONFLICT (chunk_id)
        DO UPDATE SET
            text = EXCLUDED.text,
            page_number = EXCLUDED.page_number,
            source = EXCLUDED.source,
            extraction_method = EXCLUDED.extraction_method,
            embedding = EXCLUDED.embedding;
        """

        connection = get_connection()

        try:
            with connection.cursor() as cursor:

                for chunk, embedding in zip(
                    chunks,
                    embeddings,
                ):
                    vector_string = (
                        "["
                        + ",".join(
                            str(value)
                            for value in embedding
                        )
                        + "]"
                    )

                    cursor.execute(
                        query,
                        (
                            chunk.chunk_id,
                            chunk.document_id,
                            chunk.text,
                            chunk.page_number,
                            chunk.source,
                            chunk.extraction_method,
                            vector_string,
                        ),
                    )

            connection.commit()

        finally:
            connection.close()