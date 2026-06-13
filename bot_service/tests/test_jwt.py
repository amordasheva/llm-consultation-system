import pytest
from jose import jwt

from app.core.config import settings
from app.core.jwt import InvalidTokenError, decode_and_validate


def _make_token(sub: str = "1", role: str = "user") -> str:
    return jwt.encode(
        {"sub": sub, "role": role},
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALG,
    )


def test_valid_token_returns_payload():
    token = _make_token(sub="123", role="user")
    payload = decode_and_validate(token)
    assert payload["sub"] == "123"


def test_garbage_token_raises():
    with pytest.raises(InvalidTokenError):
        decode_and_validate("not-a-real-token")