"""
OData Configuration - Configuration options for the OData client.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ODataConfig:
    """
    Configuration options for the OData client.
    
    Attributes:
        timeout: Request timeout in seconds (default: 120)
        verify_ssl: Whether to verify SSL certificates (default: True)
        max_retries: Maximum number of retry attempts (default: 3)
        retry_delay: Delay between retries in seconds (default: 1.0)
        csrf_token_refresh: Whether to refresh CSRF token on each request (default: False)
        default_page_size: Default page size for paginated requests (default: 100)
        normalize_responses: Whether to normalize V2 responses to V4 format (default: True)
    
    Example:
        >>> config = ODataConfig(
        ...     timeout=60,
        ...     verify_ssl=True,
        ...     max_retries=5,
        ... )
        >>> client = ODataClient(..., config=config)
    """
    
    timeout: int = 120
    verify_ssl: bool = True
    max_retries: int = 3
    retry_delay: float = 1.0
    csrf_token_refresh: bool = False
    default_page_size: int = 100
    normalize_responses: bool = True
    
    # Advanced options
    headers: dict = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Validate configuration values."""
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")
        if self.max_retries < 0:
            raise ValueError("max_retries cannot be negative")
        if self.retry_delay < 0:
            raise ValueError("retry_delay cannot be negative")
        if self.default_page_size <= 0:
            raise ValueError("default_page_size must be positive")
