"""
SAP OData Exceptions.

Custom exception classes for handling SAP OData errors.
"""


class SAPODataError(Exception):
    """Base exception for all SAP OData errors."""
    
    def __init__(self, message: str, **kwargs):
        self.message = message
        self.details = kwargs
        super().__init__(message)
    
    def __str__(self) -> str:
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({details_str})"
        return self.message


class SAPConnectionError(SAPODataError):
    """Raised when unable to connect to SAP system."""
    pass


class SAPAuthenticationError(SAPODataError):
    """Raised when authentication fails (invalid credentials)."""
    pass


class SAPServiceError(SAPODataError):
    """
    Raised when OData service returns an error.
    
    Attributes:
        status_code: HTTP status code from the response
        response_body: Error response body from SAP
    """
    
    def __init__(
        self,
        message: str,
        status_code: int = 0,
        response_body: str = "",
        **kwargs
    ):
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(
            message,
            status_code=status_code,
            **kwargs
        )


class SAPCSRFTokenError(SAPODataError):
    """Raised when CSRF token fetch fails."""
    pass


class SAPMetadataError(SAPODataError):
    """
    Raised when metadata fetch or parsing fails.
    
    Attributes:
        status_code: HTTP status code if available
    """
    
    def __init__(self, message: str, status_code: int = 0, **kwargs):
        self.status_code = status_code
        super().__init__(message, status_code=status_code, **kwargs)


class SAPBatchError(SAPODataError):
    """Raised when batch operation fails."""
    
    def __init__(
        self,
        message: str,
        failed_operations: list = None,
        **kwargs
    ):
        self.failed_operations = failed_operations or []
        super().__init__(message, **kwargs)
