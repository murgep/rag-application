
from pwdlib import PasswordHash


_password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Return an Argon2 password hash."""
    if not password:
        raise ValueError("Password cannot be empty.")

    return _password_hash.hash(password)


def verify_password(password: str, stored_hash: str | None) -> bool:
    """Verify a password without accepting missing password hashes."""
    if not password or not stored_hash:
        return False

    try:
        return _password_hash.verify(password, stored_hash)
    except (ValueError, TypeError):
        return False
