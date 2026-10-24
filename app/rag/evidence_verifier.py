
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
        question_lower = question.lower()

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

        import re

        evidence = " ".join(chunk.text.lower() for chunk in chunks)

        has_explicit_period = re.search(
            r"\b\d+\s+months?\b.{0,100}"
            r"\b(?:before becoming eligible for promotion|"
            r"before promotion|promotion eligibility)\b",
            evidence,
        )

        return has_explicit_period is not None
