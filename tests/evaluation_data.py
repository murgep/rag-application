
EVALUATION_CASES = [
    {
        "id": "casual_leave",
        "question": (
            "How many days of casual leave do full-time employees "
            "receive each year?"
        ),
        "relevant_chunk_ids": [
            "employee_handbook_rag_retrieval_test_v2_p2_c3",
            "employee_handbook_rag_retrieval_test_v2_p6_c1",
        ],
    },
    {
        "id": "sick_leave",
        "question": "What is the annual sick leave allowance?",
        "relevant_chunk_ids": [
            "employee_handbook_rag_retrieval_test_v2_p2_c4",
            "employee_handbook_rag_retrieval_test_v2_p6_c1",
        ],
    },
    {
        "id": "earned_leave",
        "question": "How much earned leave does an employee accrue monthly?",
        "relevant_chunk_ids": [
            "employee_handbook_rag_retrieval_test_v2_p2_c5",
            "employee_handbook_rag_retrieval_test_v2_p6_c2",
        ],
    },
    {
        "id": "remote_work",
        "question": (
            "How many remote-work days may eligible corporate employees "
            "request weekly?"
        ),
        "relevant_chunk_ids": [
            "employee_handbook_rag_retrieval_test_v2_p2_c2",
            "employee_handbook_rag_retrieval_test_v2_p6_c2",
        ],
    },
    {
        "id": "lost_laptop",
        "question": "How soon must a lost company laptop be reported?",
        "relevant_chunk_ids": [
            "employee_handbook_rag_retrieval_test_v2_p3_c6",
            "employee_handbook_rag_retrieval_test_v2_p6_c3",
        ],
    },
    {
        "id": "attendance_retention",
        "question": "How long are employee attendance records retained?",
        "relevant_chunk_ids": [
            "employee_handbook_rag_retrieval_test_v2_p5_c2",
            "employee_handbook_rag_retrieval_test_v2_p6_c4",
        ],
    },
    {
        "id": "casual_leave_paraphrase",
        "question": (
            "What is the yearly casual leave allowance for a full-time "
            "employee?"
        ),
        "relevant_chunk_ids": [
            "employee_handbook_rag_retrieval_test_v2_p2_c3",
            "employee_handbook_rag_retrieval_test_v2_p6_c1",
        ],
    },
    {
        "id": "sick_leave_paraphrase",
        "question": (
            "How many days off for illness are provided annually to "
            "employees?"
        ),
        "relevant_chunk_ids": [
            "employee_handbook_rag_retrieval_test_v2_p2_c4",
            "employee_handbook_rag_retrieval_test_v2_p6_c1",
        ],
    },
]

UNSUPPORTED_EVALUATION_CASES = [
    {
        "id": "mars_work_policy",
        "question": "What is the company's policy for working on Mars?",
    },
    {
        "id": "jupiter_underwater_offices",
        "question": "How many underwater offices does the company operate on Jupiter?",
    },
]
