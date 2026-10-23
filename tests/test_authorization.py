
from unittest.mock import MagicMock, patch

import pytest

from app.auth.authorization import (
    AuthorizationError,
    AuthorizationService,
    UserPermissions,
)


@pytest.fixture
def mock_database():
    connection = MagicMock()
    cursor = MagicMock()

    connection.cursor.return_value.__enter__.return_value = cursor

    with patch(
        "app.auth.authorization.get_connection",
        return_value=connection,
    ):
        yield connection, cursor


def test_loads_user_with_multiple_roles_and_departments(mock_database):
    connection, cursor = mock_database

    cursor.fetchone.return_value = (
        "user-001",
        "alice@example.com",
        True,
    )
    cursor.fetchall.side_effect = [
        [("employee",), ("manager",)],
        [("HR",), ("Finance",)],
    ]

    service = AuthorizationService()
    permissions = service.get_user_permissions("user-001")

    assert permissions.user_id == "user-001"
    assert permissions.email == "alice@example.com"
    assert permissions.roles == frozenset({"employee", "manager"})
    assert permissions.departments == frozenset({"HR", "Finance"})

    assert cursor.execute.call_count == 3
    connection.close.assert_called_once()


def test_missing_user_is_rejected(mock_database):
    connection, cursor = mock_database
    cursor.fetchone.return_value = None

    service = AuthorizationService()

    with pytest.raises(AuthorizationError, match="User not found"):
        service.get_user_permissions("unknown-user")

    assert cursor.execute.call_count == 1
    connection.close.assert_called_once()


def test_inactive_user_is_rejected(mock_database):
    connection, cursor = mock_database

    cursor.fetchone.return_value = (
        "user-002",
        "inactive@example.com",
        False,
    )

    service = AuthorizationService()

    with pytest.raises(
        AuthorizationError,
        match="User account is inactive",
    ):
        service.get_user_permissions("user-002")

    assert cursor.execute.call_count == 1
    connection.close.assert_called_once()


def test_department_access_is_checked_explicitly():
    service = AuthorizationService()

    permissions = UserPermissions(
        user_id="admin-001",
        email="admin@example.com",
        roles=frozenset({"admin"}),
        departments=frozenset({"HR"}),
    )

    assert service.can_access_department(permissions, "HR")
    assert not service.can_access_department(permissions, "Finance")


def test_require_department_access_rejects_unassigned_department():
    service = AuthorizationService()

    permissions = UserPermissions(
        user_id="manager-001",
        email="manager@example.com",
        roles=frozenset({"manager", "admin"}),
        departments=frozenset({"HR"}),
    )

    with pytest.raises(
        AuthorizationError,
        match="not authorized",
    ):
        service.require_department_access(permissions, "Finance")


@pytest.mark.parametrize("user_id", ["", " ", None])
def test_empty_user_identity_is_rejected(user_id):
    service = AuthorizationService()

    with pytest.raises(
        AuthorizationError,
        match="User identity is required",
    ):
        service.get_user_permissions(user_id)

def test_database_query_failure_closes_connection(mock_database):
    connection, cursor = mock_database
    cursor.execute.side_effect = RuntimeError("simulated database failure")

    service = AuthorizationService()

    with pytest.raises(RuntimeError, match="simulated database failure"):
        service.get_user_permissions("user-001")

    connection.close.assert_called_once()


def test_connection_failure_propagates():
    with patch(
        "app.auth.authorization.get_connection",
        side_effect=RuntimeError("simulated connection failure"),
    ):
        service = AuthorizationService()

        with pytest.raises(
            RuntimeError,
            match="simulated connection failure",
        ):
            service.get_user_permissions("user-001")