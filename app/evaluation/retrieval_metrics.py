
def hit_at_k(relevant: list[bool], k: int) -> int:
    if k < 0:
        raise ValueError("k must be non-negative.")

    return int(any(relevant[:k]))


def reciprocal_rank(relevant: list[bool]) -> float:
    for rank, is_relevant in enumerate(relevant, start=1):
        if is_relevant:
            return 1.0 / rank

    return 0.0


def relevance_at_ranks(
    retrieved_chunk_ids: list[str],
    relevant_chunk_ids: list[str],
) -> list[bool]:
    relevant_set = set(relevant_chunk_ids)

    return [
        chunk_id in relevant_set
        for chunk_id in retrieved_chunk_ids
    ]
