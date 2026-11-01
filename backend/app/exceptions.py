"""Custom exceptions for Vex API."""


class VexError(Exception):
    """Base exception for Vex API errors."""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ValidationError(VexError):
    """Raised when user input validation fails."""
    def __init__(self, message: str):
        super().__init__(message, status_code=400)


class AthenaError(VexError):
    """Raised when Athena query execution fails."""
    def __init__(self, message: str):
        super().__init__(message, status_code=500)


class AthenaTimeoutError(AthenaError):
    """Raised when Athena query times out."""
    def __init__(self, message: str = "Query timed out"):
        super().__init__(message)


class NotFoundError(VexError):
    """Raised when a requested resource is not found."""
    def __init__(self, message: str):
        super().__init__(message, status_code=404)


class ConfigError(VexError):
    """Raised when environment configuration is missing or invalid."""
    def __init__(self, message: str):
        super().__init__(message, status_code=500)
