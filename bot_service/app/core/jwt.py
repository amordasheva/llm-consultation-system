from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTError

from app.core.config import settings


class InvalidTokenError(Exception):
    pass


def decode_and_validate(token: str) -> dict:
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG]
        )
    except ExpiredSignatureError as exc:
        raise InvalidTokenError("Token expired") from exc
    except JWTError as exc:
        raise InvalidTokenError("Invalid token") from exc

    if "sub" not in payload:
        raise InvalidTokenError("Token has no subject")

    return payload