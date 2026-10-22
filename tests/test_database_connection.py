
from unittest.mock import patch

import psycopg
import pytest

from app.database.connection import get_connection


def test_get_connection_propagates_database_failure():
    with patch(
        "app.database.connection.psycopg.connect",
        side_effect=psycopg.OperationalError(
            "Database unavailable"
        ),
    ) as mock_connect:

        with pytest.raises(psycopg.OperationalError):
            get_connection()

    mock_connect.assert_called_once()
