
from dataclasses import dataclass

from app.database.connection import get_connection


@dataclass(frozen=True)
class UserPermissions:
    user_id: str
    email: str
    roles: frozenset[str]
    departments: frozenset[str]


class AuthorizationError(Exception):
    """Raised when a user is missing, inactive, or unauthorized."""


class AuthorizationService:
    """Load trusted user permissions from PostgreSQL."""

    def get_user_permissions(self, user_id: str) -> UserPermissions:
        if not user_id or not user_id.strip():
            raise AuthorizationError("User identity is required.")

        connection = get_connection()

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT user_id, email, is_active
                    FROM app_users
                    WHERE user_id = %s;
                    """,
                    (user_id,),
                )
                user = cursor.fetchone()

                if user is None:
                    raise AuthorizationError("User not found.")

                db_user_id, email, is_active = user

                if not is_active:
                    raise AuthorizationError("User account is inactive.")

                cursor.execute(
                    """
                    SELECT role
                    FROM user_roles
                    WHERE user_id = %s;
                    """,
                    (db_user_id,),
                )
                roles = frozenset(row[0] for row in cursor.fetchall())

                cursor.execute(
                    """
                    SELECT department
                    FROM user_department_access
                    WHERE user_id = %s;
                    """,
                    (db_user_id,),
                )
                departments = frozenset(
                    row[0] for row in cursor.fetchall()
                )

                return UserPermissions(
                    user_id=db_user_id,
                    email=email,
                    roles=roles,
                    departments=departments,
                )

        finally:
            connection.close()

    def can_access_department(
        self,
        permissions: UserPermissions,
        department: str,
    ) -> bool:
        if not department or not department.strip():
            return False

        return department in permissions.departments

    def require_department_access(
        self,
        permissions: UserPermissions,
        department: str,
    ) -> None:
        if not self.can_access_department(permissions, department):
            raise AuthorizationError(
                "You are not authorized to access this department."
            )
