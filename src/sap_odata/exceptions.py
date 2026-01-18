"""
Exceptions - Custom exceptions for OData operations.
"""

from typing import Optional


class ODataError(Exception):
    """
    Base exception for OData operations.
    
    Attributes:
        message: Error message
        status_code: HTTP status code (if applicable)
        details: Additional error details
    """
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        details: Optional[str] = None,
    ) -> None:
        """Initialize OData error."""
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)
    
    def __str__(self) -> str:
        """String representation."""
        if self.status_code:
            return f"[HTTP {self.status_code}] {self.message}"
        return self.message


class ODataConnectionError(ODataError):
    """
    Raised when unable to connect to SAP system.
    
    This can occur due to:
    - Network connectivity issues
    - Incorrect host URL
    - Firewall blocking
    - Service unavailable
    """
    pass


class ODataAuthenticationError(ODataError):
    """
    Raised when authentication fails.
    
    This can occur due to:
    - Invalid username/password
    - Locked user account
    - Missing authorizations
    - Expired credentials
    """
    
    def __init__(self, message: str = "Authentication failed") -> None:
        """Initialize authentication error."""
        super().__init__(message, status_code=401)


class ODataNotFoundError(ODataError):
    """
    Raised when requested resource is not found.
    
    This can occur when:
    - Entity doesn't exist
    - Entity set doesn't exist
    - Service doesn't exist
    - Invalid entity key
    """
    
    def __init__(self, message: str = "Resource not found") -> None:
        """Initialize not found error."""
        super().__init__(message, status_code=404)


class ODataValidationError(ODataError):
    """
    Raised when request validation fails.
    
    This can occur due to:
    - Missing required fields
    - Invalid field values
    - Constraint violations
    - Invalid filter syntax
    """
    
    def __init__(self, message: str, details: Optional[str] = None) -> None:
        """Initialize validation error."""
        super().__init__(message, status_code=400, details=details)


class ODataCSRFError(ODataError):
    """
    Raised when CSRF token handling fails.
    
    This can occur when:
    - Unable to fetch CSRF token
    - CSRF token expired
    - CSRF token invalid
    """
    
    def __init__(self, message: str = "CSRF token error") -> None:
        """Initialize CSRF error."""
        super().__init__(message, status_code=403)


class ODataBatchError(ODataError):
    """
    Raised when batch operation fails.
    
    Contains information about which operations in the batch failed.
    """
    
    def __init__(
        self,
        message: str,
        failed_operations: Optional[list] = None,
    ) -> None:
        """Initialize batch error."""
        super().__init__(message)
        self.failed_operations = failed_operations or []


class ODataMetadataError(ODataError):
    """
    Raised when metadata parsing fails.
    
    This can occur due to:
    - Invalid metadata XML
    - Unsupported metadata version
    - Missing required elements
    """
    
    def __init__(self, message: str = "Metadata parsing failed") -> None:
        """Initialize metadata error."""
        super().__init__(message)
