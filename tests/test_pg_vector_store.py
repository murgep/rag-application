
from unittest.mock import MagicMock, patch

import pytest

from app.retrieval.pg_vector_store import PostgreSQLVectorStore


@pytest.mark.parametrize("department", ["HR", "Finance"])
def test_search_filters_by_department(department):
    mock_connection = MagicMock()
    mock_cursor = MagicMock()
    mock_connection.cursor.return_value.__enter__.return_value = (
        mock_cursor
    )
    mock_cursor.fetchall.return_value = []

    store = PostgreSQLVectorStore()

    with patch(
        "app.retrieval.pg_vector_store.get_connection",
        return_value=mock_connection,
    ):
        results = store.search(
            query_embedding=[0.1, 0.2, 0.3],
            top_k=3,
            department=department,
        )

    assert results == []

    executed_calls = mock_cursor.execute.call_args_list
    assert len(executed_calls) == 2

    assert "SET LOCAL statement_timeout = '5s'" in executed_calls[0].args[0]

    executed_query = executed_calls[1].args[0]
    executed_params = executed_calls[1].args[1]

    assert "d.department = ANY(%s)" in executed_query
    assert executed_params[1] == [department]
    assert executed_params[3] == 3

    mock_connection.close.assert_called_once()


def test_search_without_department_uses_none_filter():
    mock_connection = MagicMock()
    mock_cursor = MagicMock()
    mock_connection.cursor.return_value.__enter__.return_value = (
        mock_cursor
    )
    mock_cursor.fetchall.return_value = []

    store = PostgreSQLVectorStore()

    with patch(
        "app.retrieval.pg_vector_store.get_connection",
        return_value=mock_connection,
    ):
        results = store.search(
            query_embedding=[0.1, 0.2, 0.3],
            top_k=3,
            department=None,
        )

    assert results == []

    executed_calls = mock_cursor.execute.call_args_list
    assert len(executed_calls) == 2

    executed_query = executed_calls[1].args[0]
    executed_params = executed_calls[1].args[1]

    assert "d.department = ANY(%s)" not in executed_query
    assert len(executed_params) == 3

    mock_connection.close.assert_called_once()


def test_search_filters_by_multiple_departments():
    mock_connection = MagicMock()
    mock_cursor = MagicMock()
    mock_connection.cursor.return_value.__enter__.return_value = (
        mock_cursor
    )
    mock_cursor.fetchall.return_value = []

    store = PostgreSQLVectorStore()

    with patch(
        "app.retrieval.pg_vector_store.get_connection",
        return_value=mock_connection,
    ):
        results = store.search(
            query_embedding=[0.1, 0.2, 0.3],
            top_k=5,
            departments=frozenset({"HR", "Finance"}),
        )

    assert results == []

    executed_calls = mock_cursor.execute.call_args_list
    executed_query = executed_calls[1].args[0]
    executed_params = executed_calls[1].args[1]

    assert "d.department = ANY(%s)" in executed_query
    assert executed_params[1] == ["Finance", "HR"]
    assert executed_params[3] == 5

    mock_connection.close.assert_called_once()


def test_search_with_empty_department_allowlist_returns_no_results():
    store = PostgreSQLVectorStore()

    with patch(
        "app.retrieval.pg_vector_store.get_connection"
    ) as mock_get_connection:
        results = store.search(
            query_embedding=[0.1, 0.2, 0.3],
            top_k=3,
            departments=frozenset(),
        )

    assert results == []
    mock_get_connection.assert_not_called()


def test_search_rejects_both_department_filter_modes():
    store = PostgreSQLVectorStore()

    with pytest.raises(ValueError, match="either department or departments"):
        store.search(
            query_embedding=[0.1, 0.2, 0.3],
            department="HR",
            departments=frozenset({"HR", "Finance"}),
        )
