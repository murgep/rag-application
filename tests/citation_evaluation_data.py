
CITATION_EVALUATION_CASES = [
    {
        "id": "annual_leave_supported",
        "claim": "Employees receive 24 days of paid annual leave.",
        "evidence": "Employees receive 24 days of paid annual leave.",
        "supported": True,
    },
    {
        "id": "promotion_period_unsupported",
        "claim": (
            "Employees become eligible for promotion after 12 months."
        ),
        "evidence": (
            "Promotion decisions consider demonstrated capability, "
            "sustained performance, role availability, and approval "
            "from the department head. Time in role alone does not "
            "guarantee promotion."
        ),
        "supported": False,
    },
    {
        "id": "annual_leave_paraphrase",
        "claim": (
            "Full-time staff are entitled to 24 paid leave days annually."
        ),
        "evidence": (
            "Employees receive 24 days of paid annual leave."
        ),
        "supported": True,
    },
    {
        "id": "unsupported_bonus_percentage",
        "claim": (
            "Employees receive an annual performance bonus of 15%."
        ),
        "evidence": (
            "Formal performance reviews take place twice each year, "
            "in June and December."
        ),
        "supported": False,
    },
    {
        "id": "contradictory_leave_claim",
        "claim": "Employees receive 30 days of paid annual leave.",
        "evidence": (
            "Employees receive 24 days of paid annual leave."
        ),
        "supported": False,
    },
    {
        "id": "partially_supported_claim",
        "claim": (
            "Employees receive 24 days of annual leave and a 15% bonus."
        ),
        "evidence": (
            "Employees receive 24 days of paid annual leave."
        ),
        "supported": False,
    },
]
