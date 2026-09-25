class ApplicationError(Exception):
    """Base exception for expected application errors."""


class ResourceNotFoundError(ApplicationError):
    """Raised when a requested resource does not exist."""


class ValidationError(ApplicationError):
    """Raised when application-level validation fails."""


class AuthorizationError(ApplicationError):
    """Raised when an operation is not authorized."""