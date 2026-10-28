
from app.models.schemas import RAGSource


def validate_citation_references(
    sources: list[RAGSource],
    retrieved_chunks: list[dict],
) -> dict[str, int | bool]:
    """
    Validate that each returned source matches a retrieved chunk's
    document ID, source filename, and page number.

    This checks traceability, not semantic claim support.
    """
    retrieved_references = {
        (
            chunk["document_id"],
            chunk["source"],
            chunk["page_number"],
        )
        for chunk in retrieved_chunks
    }

    valid_count = sum(
        (
            source.document_id,
            source.source,
            source.page_number,
        ) in retrieved_references
        for source in sources
    )

    total = len(sources)

    return {
        "total_citations": total,
        "valid_citations": valid_count,
        "invalid_citations": total - valid_count,
        "all_valid": valid_count == total,
    }
