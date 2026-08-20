from app.models.schemas import (
    DocumentChunk,
    ParsedDocument,
)


def chunk_page(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[str]:
    """
    Split page text into overlapping word-based chunks.
    """

    words = text.split()

    if not words:
        return []

    if overlap >= chunk_size:
        raise ValueError(
            "overlap must be smaller than chunk_size"
        )

    chunks = []

    start = 0

    while start < len(words):
        end = start + chunk_size

        chunk_words = words[start:end]

        chunks.append(" ".join(chunk_words))

        if end >= len(words):
            break

        start = end - overlap

    return chunks

def chunk_document(
    document: ParsedDocument,
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[DocumentChunk]:
    """
    Convert a ParsedDocument into DocumentChunk objects.
    """

    chunks = []

    for page in document.pages:

        page_chunks = chunk_page(
            page.text,
            chunk_size=chunk_size,
            overlap=overlap,
        )

        for chunk_index, chunk_text in enumerate(
            page_chunks,
            start=1,
        ):
            chunk_id = (
                f"{document.metadata.document_id}"
                f"_p{page.page_number}"
                f"_c{chunk_index}"
            )

            chunk = DocumentChunk(
                chunk_id=chunk_id,
                document_id=document.metadata.document_id,
                text=chunk_text,
                page_number=page.page_number,
                source=document.metadata.source,
                extraction_method=page.extraction_method,
            )

            chunks.append(chunk)

    return chunks