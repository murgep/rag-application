from app.models.schemas import DocumentChunk
from app.rag.evidence_verifier import PromotionPeriodVerifier


def make_chunk(text: str) -> DocumentChunk:
    return DocumentChunk(
        chunk_id="test-chunk-001",
        document_id="employee-handbook",
        text=text,
        page_number=4,
        source="employee_handbook.pdf",
        extraction_method="text",
    )


def test_rejects_promotion_passage_without_minimum_period():
    verifier = PromotionPeriodVerifier()

    chunks = [
        make_chunk(
            "Promotion decisions consider demonstrated capability "
            "at the next level, sustained performance, role "
            "availability, and approval from the department head. "
            "Time in role alone does not guarantee promotion."
        )
    ]

    assert not verifier.is_sufficient(
        question=(
            "What minimum number of months must an employee work "
            "before becoming eligible for promotion?"
        ),
        chunks=chunks,
    )


def test_accepts_promotion_passage_with_explicit_minimum_period():
    verifier = PromotionPeriodVerifier()

    chunks = [
        make_chunk(
            "Employees must complete 12 months in their current role "
            "before becoming eligible for promotion."
        )
    ]

    assert verifier.is_sufficient(
        question=(
            "What minimum number of months must an employee work "
            "before becoming eligible for promotion?"
        ),
        chunks=chunks,
    )


def test_accepts_non_promotion_question_with_evidence():
    verifier = PromotionPeriodVerifier()

    chunks = [
        make_chunk(
            "Employees receive 24 days of paid annual leave."
        )
    ]

    assert verifier.is_sufficient(
        question="How many annual leave days do employees receive?",
        chunks=chunks,
    )


def test_rejects_empty_evidence_for_promotion_question():
    verifier = PromotionPeriodVerifier()

    assert not verifier.is_sufficient(
        question=(
            "What minimum number of months must an employee work "
            "before becoming eligible for promotion?"
        ),
        chunks=[],
    )


def test_rejects_unrelated_month_period_for_promotion_question():
    verifier = PromotionPeriodVerifier()

    chunks = [
        make_chunk(
            "Employees receive a performance review every 12 months. "
            "Promotion decisions depend on performance and role availability."
        )
    ]

    assert not verifier.is_sufficient(
        question=(
            "What minimum number of months must an employee work "
            "before becoming eligible for promotion?"
        ),
        chunks=chunks,
    )


def test_accepts_alternative_promotion_period_wording():
    verifier = PromotionPeriodVerifier()

    chunks = [
        make_chunk(
            "An employee becomes eligible for promotion after "
            "completing 12 months in the current position."
        )
    ]

    assert verifier.is_sufficient(
        question=(
            "What minimum number of months must an employee work "
            "before becoming eligible for promotion?"
        ),
        chunks=chunks,
    )


def test_rejects_empty_evidence_for_non_promotion_question():
    verifier = PromotionPeriodVerifier()

    assert not verifier.is_sufficient(
        question="How many annual leave days do employees receive?",
        chunks=[],
    )