
def evaluate_citation_support(
    cases: list[dict],
) -> dict[str, int | float]:
    """
    Evaluate exact-text matching against manually labeled examples.

    This is a baseline, not a general semantic-support evaluator.
    """
    if not cases:
        raise ValueError("Evaluation cases cannot be empty.")

    true_positive = 0
    true_negative = 0
    false_positive = 0
    false_negative = 0

    for case in cases:
        evidence = case["evidence"].casefold()
        claim = case["claim"].casefold()
        expected_support = case["supported"]

        predicted_support = claim in evidence

        if predicted_support and expected_support:
            true_positive += 1
        elif not predicted_support and not expected_support:
            true_negative += 1
        elif predicted_support and not expected_support:
            false_positive += 1
        else:
            false_negative += 1

    total = len(cases)
    correct = true_positive + true_negative

    return {
        "total_cases": total,
        "correct_predictions": correct,
        "accuracy": correct / total,
        "true_positive": true_positive,
        "true_negative": true_negative,
        "false_positive": false_positive,
        "false_negative": false_negative,
    }
