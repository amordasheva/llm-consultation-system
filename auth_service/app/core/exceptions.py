from fastapi import HTTPException


class BaseHTTPException(HTTPException):
    status_code = 400
    detail = "Bad request"

    def __init__(self, detail: str | None = None):
        super().__init__(status_code=self.status_code, detail=detail or self.detail)


class UserAlreadyExistsError(BaseHTTPException):
    status_code = 409
    detail = "User already exists"


class InvalidCredentialsError(BaseHTTPException):
    status_code = 401
    detail = "Invalid credentials"


class InvalidTokenError(BaseHTTPException):
    status_code = 401
    detail = "Invalid token"


class TokenExpiredError(BaseHTTPException):
    status_code = 401
    detail = "Token expired"


class UserNotFoundError(BaseHTTPException):
    status_code = 404
    detail = "User not found"


class PermissionDeniedError(BaseHTTPException):
    status_code = 403
    detail = "Permission denied"