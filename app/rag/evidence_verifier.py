
from typing import Protocol

from app.models.schemas import DocumentChunk


ABSTENTION_ANSWER = (
    "I don't have enough information in the provided "
    "documents to answer this question."
)


class EvidenceVerifier(Protocol):
    """Checks whether evidence supports the requested answer."""

    def is_sufficient(
        self,
        question: str,
        chunks: list[DocumentChunk],
    ) -> bool:
        ...


class AlwaysSufficientVerifier:
    """Compatibility verifier; accepts any non-empty evidence."""

    def is_sufficient(
        self,
        question: str,
        chunks: list[DocumentChunk],
    ) -> bool:
        return bool(chunks)



class PromotionPeriodVerifier:
    """Narrow verifier for promotion-period questions."""

    def is_sufficient(
        self,
        question: str,
        chunks: list[DocumentChunk],
    ) -> bool:
        import re

        question_lower = question.casefold()

        asks_for_promotion_period = (
            "promotion" in question_lower
            and any(
                phrase in question_lower
                for phrase in (
                    "how many months",
                    "minimum number of months",
                    "minimum months",
                    "before becoming eligible",
                )
            )
        )

        if not asks_for_promotion_period:
            return bool(chunks)

        if not chunks:
            return False

        evidence = " ".join(
            chunk.text.casefold()
            for chunk in chunks
        )

        # Recognize explicit month-based promotion eligibility statements
        # with either the period before or after the eligibility wording.
        patterns = (
            r"\b\d+\s+months?\b.{0,100}"
            r"\b(?:before becoming eligible for promotion|"
            r"before promotion|promotion eligibility)\b",

            r"\b(?:eligible for promotion|"
            r"eligibility for promotion)\b.{0,100}"
            r"\b(?:after|upon|following|completion of)\b"
            r".{0,40}\b\d+\s+months?\b",

            r"\bpromotion\b.{0,100}"
            r"\bafter completing\s+\d+\s+months?\b",
        )

        return any(
            re.search(pattern, evidence) is not None
            for pattern in patterns
        )
def test_rejects_unrelated_month_period_for_promotion_question():
    verifier = PromotionPeriodVerifier()

    chunks = [
        make_chunk(
            "Employees receive a performance review every 12 months. "
            "Promotion decisions depend on demonstrated capability, "
            "sustained performance, role availability, and approval."
        )
    ]

    assert not verifier.is_sufficient(
        question=(
            "What minimum number of months must an employee work "
            "before becoming eligible for promotion?"
        ),
        chunks=chunks,
    )

def test_current_verifier_does_not_detect_contradictory_evidence():
    verifier = PromotionPeriodVerifier()

    chunks = [
        make_chunk(
            "Employees become eligible for promotion after "
            "completing 12 months in their current position. "
            "This requirement was discontinued last year."
        )
    ]

    # Documents the current limitation: regex matching finds the
    # eligibility statement but does not understand the contradiction.
    assert verifier.is_sufficient(
        question=(
            "What minimum number of months must an employee work "
            "before becoming eligible for promotion?"
        ),
        chunks=chunks,
    )