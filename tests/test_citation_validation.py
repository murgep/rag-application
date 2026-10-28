
from app.evaluation.citation_validation import (
    validate_citation_references,
)
from app.models.schemas import RAGSource


def test_valid_citation_matches_retrieved_chunk():
    sources = [
        RAGSource(
            document_id="hr-policy",
            source="hr_policy.pdf",
            page_number=2,
            similarity=0.95,
        )
    ]

    chunks = [
        {
            "document_id": "hr-policy",
            "source": "hr_policy.pdf",
            "page_number": 2,
        }
    ]

    result = validate_citation_references(sources, chunks)

    assert result == {
        "total_citations": 1,
        "valid_citations": 1,
        "invalid_citations": 0,
        "all_valid": True,
    }


def test_invalid_page_reference_is_detected():
    sources = [
        RAGSource(
            document_id="hr-policy",
            source="hr_policy.pdf",
            page_number=9,
            similarity=0.95,
        )
    ]

    chunks = [
        {
            "document_id": "hr-policy",
            "source": "hr_policy.pdf",
            "page_number": 2,
        }
    ]

    result = validate_citation_references(sources, chunks)

    assert result["valid_citations"] == 0
    assert result["invalid_citations"] == 1
    assert result["all_valid"] is False


def test_empty_citation_list_is_not_marked_as_grounded():
    result = validate_citation_references([], [])

    assert result["total_citations"] == 0
    assert result["valid_citations"] == 0
    assert result["invalid_citations"] == 0
    assert result["all_valid"] is True
