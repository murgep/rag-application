
from app.auth.passwords import hash_password, verify_password


def test_password_is_hashed_and_can_be_verified():
    password = "Local-Development-Passphrase-123!"
    stored_hash = hash_password(password)

    assert stored_hash != password
    assert verify_password(password, stored_hash)


def test_wrong_password_is_rejected():
    stored_hash = hash_password("Correct-Passphrase-123!")

    assert not verify_password("Incorrect-Passphrase-123!", stored_hash)


def test_missing_hash_is_rejected():
    assert not verify_password("Some-Passphrase-123!", None)


def test_empty_password_cannot_be_hashed():
    import pytest

    with pytest.raises(ValueError):
        hash_password("")
