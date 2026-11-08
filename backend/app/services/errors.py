"""Domain errors raised by services and rendered by one FastAPI handler."""

from typing import Any


class DomainError(Exception):
    code: str = "DOMAIN_ERROR"
    status_code: int = 400

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details: dict[str, Any] = details or {}

    def to_payload(self) -> dict[str, Any]:
        return {
            "ok": False,
            "error": {"code": self.code, "message": self.message, "details": self.details},
        }


class NotFoundError(DomainError):
    code = "NOT_FOUND"
    status_code = 404


class ValidationFailedError(DomainError):
    code = "VALIDATION_FAILED"
    status_code = 422
