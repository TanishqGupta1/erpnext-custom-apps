class ZiFlowError(Exception):
    """Raised when ZiFlow API returns an error response."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class MissingConfigurationError(Exception):
    """Raised when required settings are absent."""

    def __init__(self, message: str):
        super().__init__(message)
