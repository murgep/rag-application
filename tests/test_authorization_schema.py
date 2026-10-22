
from unittest.mock import MagicMock, patch

import pytest

from app.database import schema


@pytest.fixture
def mock_database():
    connection = MagicMock()
    cursor = MagicMock()

    connection.cursor.return_value.__enter__.return_value = cursor

    with patch(
        "app.database.schema.get_connection",
        return_value=connection,
    ):
        yield connection, cursor


def test_create_schema_creates_authorization_tables(mock_database):
    connection, cursor = mock_database

    schema.create_schema()

    executed_sql = [
        call.args[0]
        for call in cursor.execute.call_args_list
    ]

    combined_sql = "\n".join(executed_sql)

    assert "CREATE TABLE IF NOT EXISTS app_users" in combined_sql
    assert "CREATE TABLE IF NOT EXISTS user_roles" in combined_sql
    assert (
        "CREATE TABLE IF NOT EXISTS user_department_access"
        in combined_sql
    )

    connection.commit.assert_called_once()
    connection.close.assert_called_once()


def test_user_roles_support_multiple_roles_and_validate_role_names():
    sql = schema.CREATE_USER_ROLES_TABLE

    assert "PRIMARY KEY (user_id, role)" in sql
    assert "'employee', 'manager', 'admin'" in sql
    assert "FOREIGN KEY (user_id)" in sql


def test_department_access_prevents_duplicate_assignments():
    sql = schema.CREATE_USER_DEPARTMENT_ACCESS_TABLE

    assert "PRIMARY KEY (user_id, department)" in sql
    assert "FOREIGN KEY (user_id)" in sql
    assert "CHECK (LENGTH(TRIM(department)) > 0)" in sql


def test_app_users_requires_unique_email():
    sql = schema.CREATE_APP_USERS_TABLE

    assert "email TEXT NOT NULL UNIQUE" in sql
    assert "is_active BOOLEAN NOT NULL DEFAULT TRUE" in sql
