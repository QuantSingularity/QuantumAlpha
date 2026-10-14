from typing import Any, Dict, Optional


class AIEngineError(Exception):
    status_code = 500
    code = "AI_ENGINE_ERROR"

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: Optional[int] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}
        if status_code is not None:
            self.status_code = status_code

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "error": self.message,
            "code": self.code,
            "status_code": self.status_code,
        }
        if self.details:
            payload["details"] = self.details
        return payload


class ValidationError(AIEngineError):
    status_code = 400
    code = "VALIDATION_ERROR"


class AuthenticationError(AIEngineError):
    status_code = 401
    code = "AUTHENTICATION_FAILED"


class NotFoundError(AIEngineError):
    status_code = 404
    code = "NOT_FOUND"


class ConflictError(AIEngineError):
    status_code = 409
    code = "CONFLICT"


class NotTrainedError(ConflictError):
    code = "MODEL_NOT_TRAINED"


class DependencyError(AIEngineError):
    status_code = 502
    code = "UPSTREAM_ERROR"


class DataError(AIEngineError):
    status_code = 422
    code = "INSUFFICIENT_DATA"


class ServiceError(AIEngineError):
    status_code = 500
    code = "SERVICE_ERROR"
