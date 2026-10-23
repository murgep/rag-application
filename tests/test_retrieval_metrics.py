
def hit_at_k(relevant, k):
    return int(any(relevant[:k]))


def reciprocal_rank(relevant):
    for rank, is_relevant in enumerate(relevant, start=1):
        if is_relevant:
            return 1 / rank
    return 0.0


def relevance_at_ranks(retrieved_chunk_ids, relevant_chunk_ids):
    relevant_set = set(relevant_chunk_ids)
    return [
        chunk_id in relevant_set
        for chunk_id in retrieved_chunk_ids
    ]


def test_hit_at_k_finds_relevant_result():
    assert hit_at_k([False, True, False], 3) == 1


def test_hit_at_k_returns_zero_when_no_relevant_result():
    assert hit_at_k([False, False, False], 3) == 0


def test_reciprocal_rank_rewards_first_position():
    assert reciprocal_rank([True, False, False]) == 1.0


def test_reciprocal_rank_handles_lower_rank():
    assert reciprocal_rank([False, True, False]) == 0.5


def test_reciprocal_rank_returns_zero_when_not_found():
    assert reciprocal_rank([False, False, False]) == 0.0


def test_relevance_at_ranks_matches_chunk_ids():
    retrieved = ["chunk-b", "chunk-a", "chunk-c"]
    relevant = ["chunk-a", "chunk-c"]

    assert relevance_at_ranks(retrieved, relevant) == [
        False, True, True
    ]
