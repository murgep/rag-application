
import argparse
import getpass
import re
import sys

from app.auth.passwords import hash_password
from app.database.connection import get_connection


VALID_ROLES = {"employee", "manager", "admin"}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Create a local RAG application user."
    )
    parser.add_argument("--user-id", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument(
        "--roles",
        nargs="+",
        required=True,
        choices=sorted(VALID_ROLES),
    )
    parser.add_argument(
        "--departments",
        nargs="+",
        required=True,
        help="Explicit departments this user may access.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    user_id = args.user_id.strip()
    email = args.email.strip().lower()
    departments = sorted({item.strip() for item in args.departments})

    if not user_id or not email or not departments:
        sys.exit("User ID, email, and departments must not be empty.")

    if any(not department for department in departments):
        sys.exit("Department names must not be empty.")

    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        sys.exit("Please provide a valid email address.")

    password = getpass.getpass("New password (minimum 12 characters): ")
    confirmation = getpass.getpass("Confirm password: ")

    if len(password) < 12:
        sys.exit("Password must contain at least 12 characters.")

    if password != confirmation:
        sys.exit("Passwords do not match.")

    password_hash = hash_password(password)

    # Avoid retaining the plaintext password beyond this point.
    del password, confirmation

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO app_users (user_id, email, password_hash)
                VALUES (%s, %s, %s);
                """,
                (user_id, email, password_hash),
            )

            cursor.executemany(
                """
                INSERT INTO user_roles (user_id, role)
                VALUES (%s, %s);
                """,
                [(user_id, role) for role in sorted(set(args.roles))],
            )

            cursor.executemany(
                """
                INSERT INTO user_department_access (user_id, department)
                VALUES (%s, %s);
                """,
                [(user_id, department) for department in departments],
            )

        connection.commit()
        print(f"Created user {user_id!r} with explicit department access.")

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    main()
