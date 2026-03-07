from fastapi import status


class AppException(Exception):
    """Base exception for all custom application errors."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_ERROR",
        headers: dict[str, str] | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.headers = headers
        super().__init__(self.message)


class NotFoundError(AppException):
    """Raised when a requested resource is not found."""

    def __init__(
        self, message: str = "Resource not found", error_code: str = "NOT_FOUND"
    ):
        super().__init__(
            message, status_code=status.HTTP_404_NOT_FOUND, error_code=error_code
        )


class PermissionDeniedError(AppException):
    """Raised when the user does not have permission to perform an action."""

    def __init__(
        self, message: str = "Permission denied", error_code: str = "PERMISSION_DENIED"
    ):
        super().__init__(
            message, status_code=status.HTTP_403_FORBIDDEN, error_code=error_code
        )


class AuthenticationError(AppException):
    """Raised when authentication fails (e.g. invalid credentials or token)."""

    def __init__(
        self,
        message: str = "Authentication failed",
        error_code: str = "AUTHENTICATION_ERROR",
        headers: dict[str, str] | None = None,
    ):
        if headers is None:
            headers = {"WWW-Authenticate": "Bearer"}
        super().__init__(
            message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code=error_code,
            headers=headers,
        )


class InvalidOperationError(AppException):
    """Raised when a business logic rule prevents an operation."""

    def __init__(
        self, message: str = "Invalid operation", error_code: str = "INVALID_OPERATION"
    ):
        super().__init__(
            message, status_code=status.HTTP_400_BAD_REQUEST, error_code=error_code
        )


class ValidationError(AppException):
    """Raised when data validation fails."""

    def __init__(
        self, message: str = "Validation error", error_code: str = "VALIDATION_ERROR"
    ):
        super().__init__(
            message,
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            error_code=error_code,
        )


class ResourceConflictError(AppException):
    """Raised when there is a conflict, such as a duplicate resource."""

    def __init__(
        self, message: str = "Resource conflict", error_code: str = "RESOURCE_CONFLICT"
    ):
        super().__init__(
            message, status_code=status.HTTP_409_CONFLICT, error_code=error_code
        )
