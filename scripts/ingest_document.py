"""Ingest a PDF, TXT, or DOCX file into PostgreSQL + pgvector.

Run from the repository root with the project's virtual environment active.
The script uses the existing parser, chunker, Gemini embedder, and database schema.
"""

import argparse
import logging
from pathlib import Path

from app.database.connection import get_connection
from app.embeddings.embedder import Embedder
from app.ingestion.chunker import chunk_document
from app.ingestion.parser import parse_document
from app.models.schemas import DocumentChunk


logger = logging.getLogger("ingest_document")
EMBEDDING_DIMENSIONS = 1536
EMBEDDING_BATCH_SIZE = 32


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Parse, chunk, embed, and store a document."
    )
    parser.add_argument("file", help="Path to a PDF, TXT, or DOCX file.")
    parser.add_argument(
        "--department",
        required=True,
        help="Department allowed to retrieve this document, e.g. HR or Finance.",
    )
    parser.add_argument(
        "--status",
        choices=("active", "inactive"),
        default="active",
        help="Whether the document is active for retrieval (default: active).",
    )
    parser.add_argument(
        "--effective-date",
        default=None,
        help="Optional effective date in YYYY-MM-DD format.",
    )
    parser.add_argument(
        "--shared",
        action="store_true",
        help=(
            "Make the document accessible across departments. "
            "Use only when this is intentional."
        ),
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=500,
        help="Words per chunk (default: 500).",
    )
    parser.add_argument(
        "--overlap",
        type=int,
        default=50,
        help="Overlapping words between chunks (default: 50).",
    )
    return parser.parse_args()


def generate_embeddings(embedder: Embedder, chunks: list[DocumentChunk]) -> list[list[float]]:
    """Embed chunks in small batches and validate output dimensions."""
    embeddings: list[list[float]] = []

    for start in range(0, len(chunks), EMBEDDING_BATCH_SIZE):
        batch = chunks[start : start + EMBEDDING_BATCH_SIZE]
        batch_embeddings = embedder.embed_texts([chunk.text for chunk in batch])

        if len(batch_embeddings) != len(batch):
            raise RuntimeError(
                f"Expected {len(batch)} embeddings, received {len(batch_embeddings)}."
            )

        for embedding in batch_embeddings:
            if len(embedding) != EMBEDDING_DIMENSIONS:
                raise RuntimeError(
                    "Embedding dimension mismatch: "
                    f"expected {EMBEDDING_DIMENSIONS}, received {len(embedding)}."
                )

        embeddings.extend(batch_embeddings)

    return embeddings


def persist_document(
    *,
    document_id: str,
    filename: str,
    file_type: str,
    source: str,
    department: str,
    status: str,
    effective_date: str | None,
    is_shared: bool,
    chunks: list[DocumentChunk],
    embeddings: list[list[float]],
) -> None:
    """Replace a document's chunks and metadata in one database transaction."""
    if len(chunks) != len(embeddings):
        raise ValueError("Number of chunks must match number of embeddings.")

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO documents (
                    document_id, filename, file_type, source,
                    department, status, effective_date, is_shared
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (document_id)
                DO UPDATE SET
                    filename = EXCLUDED.filename,
                    file_type = EXCLUDED.file_type,
                    source = EXCLUDED.source,
                    department = EXCLUDED.department,
                    status = EXCLUDED.status,
                    effective_date = EXCLUDED.effective_date,
                    is_shared = EXCLUDED.is_shared;
                """,
                (
                    document_id,
                    filename,
                    file_type,
                    source,
                    department,
                    status,
                    effective_date,
                    is_shared,
                ),
            )

            # Remove old chunks only after parsing and embedding succeeded.
            # The transaction ensures a failed insert rolls this deletion back.
            cursor.execute(
                "DELETE FROM chunks WHERE document_id = %s;",
                (document_id,),
            )

            for chunk, embedding in zip(chunks, embeddings):
                vector_string = "[" + ",".join(str(value) for value in embedding) + "]"
                cursor.execute(
                    """
                    INSERT INTO chunks (
                        chunk_id, document_id, text, page_number,
                        source, extraction_method, embedding
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s::vector);
                    """,
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
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    args = parse_args()

    file_path = Path(args.file).expanduser().resolve()
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(f"Input file does not exist: {file_path}")

    if args.chunk_size <= 0:
        raise ValueError("--chunk-size must be greater than zero.")
    if args.overlap < 0 or args.overlap >= args.chunk_size:
        raise ValueError("--overlap must be >= 0 and smaller than --chunk-size.")
    if not args.department.strip():
        raise ValueError("--department cannot be empty.")

    logger.info("Parsing document: %s", file_path)
    document = parse_document(str(file_path))

    chunks = chunk_document(
        document,
        chunk_size=args.chunk_size,
        overlap=args.overlap,
    )
    if not chunks:
        raise ValueError(
            "No text chunks were produced. Check whether the document contains "
            "extractable text or whether OCR is configured correctly."
        )

    logger.info(
        "Parsed document_id=%s pages=%d chunks=%d",
        document.metadata.document_id,
        len(document.pages),
        len(chunks),
    )

    embedder = Embedder()
    embeddings = generate_embeddings(embedder, chunks)

    persist_document(
        document_id=document.metadata.document_id,
        filename=document.metadata.filename,
        file_type=document.metadata.file_type,
        source=document.metadata.source,
        department=args.department.strip(),
        status=args.status,
        effective_date=args.effective_date,
        is_shared=args.shared,
        chunks=chunks,
        embeddings=embeddings,
    )

    logger.info(
        "Ingestion completed successfully: document_id=%s chunks_saved=%d "
        "department=%s status=%s shared=%s",
        document.metadata.document_id,
        len(chunks),
        args.department.strip(),
        args.status,
        args.shared,
    )


if __name__ == "__main__":
    main()
