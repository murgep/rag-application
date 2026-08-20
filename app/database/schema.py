from app.database.connection import get_connection


CREATE_DOCUMENTS_TABLE = """
CREATE TABLE IF NOT EXISTS documents (
    document_id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    source TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""


CREATE_CHUNKS_TABLE = """
CREATE TABLE IF NOT EXISTS chunks (
    chunk_id TEXT PRIMARY KEY,

    document_id TEXT NOT NULL,

    text TEXT NOT NULL,

    page_number INTEGER NOT NULL,

    source TEXT NOT NULL,

    extraction_method TEXT NOT NULL,

    embedding vector(1536),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_chunks_document
        FOREIGN KEY (document_id)
        REFERENCES documents(document_id)
        ON DELETE CASCADE
);
"""


CREATE_CHUNKS_INDEX = """
CREATE INDEX IF NOT EXISTS idx_chunks_document_id
ON chunks(document_id);
"""


def create_schema() -> None:
    """
    Create the database tables and indexes.
    """

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            # Enable pgvector.
            cursor.execute(
                "CREATE EXTENSION IF NOT EXISTS vector;"
            )

            # Create documents table.
            cursor.execute(
                CREATE_DOCUMENTS_TABLE
            )

            # Create chunks table.
            cursor.execute(
                CREATE_CHUNKS_TABLE
            )

            # Create document lookup index.
            cursor.execute(
                CREATE_CHUNKS_INDEX
            )

        connection.commit()

    finally:
        connection.close()