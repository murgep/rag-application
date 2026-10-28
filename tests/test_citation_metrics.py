
import pytest

from app.evaluation.citation_metrics import evaluate_citation_support
from tests.citation_evaluation_data import CITATION_EVALUATION_CASES



def test_citation_evaluator_matches_baseline_labels():
    result = evaluate_citation_support(CITATION_EVALUATION_CASES)

    assert result["total_cases"] == 6
    assert result["correct_predictions"] == 5
    assert result["accuracy"] == 5 / 6
    assert result["true_positive"] == 1
    assert result["true_negative"] == 4
    assert result["false_positive"] == 0
    assert result["false_negative"] == 1



def test_citation_evaluator_rejects_empty_dataset():
    with pytest.raises(ValueError, match="cannot be empty"):
        evaluate_citation_support([])


def test_exact_match_baseline_exposes_paraphrase_limitation():
    cases = [
        {
            "id": "annual_leave_paraphrase",
            "claim": (
                "Full-time staff are entitled to 24 paid leave days annually."
            ),
            "evidence": (
                "Employees receive 24 days of paid annual leave."
            ),
            "supported": True,
        }
    ]

    result = evaluate_citation_support(cases)

    assert result["correct_predictions"] == 0
    assert result["accuracy"] == 0.0
    assert result["true_positive"] == 0
    assert result["true_negative"] == 0
    assert result["false_positive"] == 0
    assert result["false_negative"] == 1
