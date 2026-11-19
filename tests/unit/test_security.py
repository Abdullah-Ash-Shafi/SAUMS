"""Unit tests for authentication security utilities (hashing, JWT)."""
from datetime import timedelta
import pytest
import jwt

from suams.auth.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_access_token,
)
from suams.config import settings


def test_password_hashing_and_verification() -> None:
    """Test bcrypt hashing and verification functions."""
    plain = "SecurePass123!"
    hashed = get_password_hash(plain)

    assert hashed != plain
    assert verify_password(plain, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_create_and_decode_access_token() -> None:
    """Test generating and decoding JWT tokens."""
    data = {"sub": "student1", "role": "Student", "user_id": 10}
    token = create_access_token(data=data, expires_delta=timedelta(minutes=15))

    decoded = decode_access_token(token)
    assert decoded["sub"] == "student1"
    assert decoded["role"] == "Student"
    assert decoded["user_id"] == 10
    assert "exp" in decoded


def test_decode_expired_token_raises_error() -> None:
    """Test expired tokens fail validation."""
    data = {"sub": "student1", "role": "Student"}
    # Token that expired 5 minutes ago
    token = create_access_token(data=data, expires_delta=timedelta(minutes=-5))

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token)


def test_decode_invalid_token_raises_error() -> None:
    """Test malformed tokens fail validation."""
    with pytest.raises(jwt.PyJWTError):
        decode_access_token("this.is.not.a.valid.jwt")
