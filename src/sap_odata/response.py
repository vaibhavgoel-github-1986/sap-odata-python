"""
SAP OData Response wrapper.

Provides a consistent response object for all OData operations.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class ODataResponse:
    """
    Unified response object for OData operations.
    
    Normalizes V2 and V4 responses to a consistent structure,
    making it easy to work with data regardless of OData version.
    
    Attributes:
        status_code: HTTP status code of the response
        data: Normalized response data with 'value' array
        raw_response: Original response data for debugging
        count: Total count if $count was requested
        next_link: Pagination link if more data is available
    
    Example:
        >>> response = client.call_odata(...)
        >>> 
        >>> # Access normalized data
        >>> for item in response.value:
        ...     print(item['CustomerID'])
        >>> 
        >>> # Check if successful
        >>> if response.is_success:
        ...     print(f"Got {len(response.value)} records")
        >>> 
        >>> # Pagination
        >>> if response.has_more:
        ...     print(f"Next page: {response.next_link}")
    """
    
    status_code: int
    data: Dict[str, Any]
    raw_response: Any = None
    count: Optional[int] = None
    next_link: Optional[str] = None
    
    @property
    def value(self) -> List[Dict[str, Any]]:
        """
        Get the response data as a list.
        
        Returns:
            List of entity dictionaries
        """
        return self.data.get("value", [])
    
    @property
    def first(self) -> Optional[Dict[str, Any]]:
        """
        Get the first entity from the response.
        
        Returns:
            First entity dict, or None if empty
        """
        values = self.value
        return values[0] if values else None
    
    @property
    def is_success(self) -> bool:
        """
        Check if the response indicates success.
        
        Returns:
            True if status code is 2xx
        """
        return 200 <= self.status_code < 300
    
    @property
    def is_empty(self) -> bool:
        """
        Check if the response contains no data.
        
        Returns:
            True if value array is empty
        """
        return len(self.value) == 0
    
    @property
    def has_more(self) -> bool:
        """
        Check if there are more pages of data available.
        
        Returns:
            True if next_link is present
        """
        return bool(self.next_link)
    
    def __len__(self) -> int:
        """Return number of entities in response."""
        return len(self.value)
    
    def __iter__(self):
        """Iterate over response entities."""
        return iter(self.value)
    
    def __getitem__(self, key):
        """Get entity by index or key."""
        if isinstance(key, int):
            return self.value[key]
        return self.data.get(key)
    
    def __bool__(self) -> bool:
        """Response is truthy if successful and has data."""
        return self.is_success and not self.is_empty
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert response to dictionary.
        
        Returns:
            Dictionary representation of the response
        """
        return {
            "status_code": self.status_code,
            "data": self.data,
            "count": self.count,
            "next_link": self.next_link,
            "is_success": self.is_success,
            "record_count": len(self.value),
        }
    
    def __repr__(self) -> str:
        return (
            f"ODataResponse(status_code={self.status_code}, "
            f"records={len(self.value)}, "
            f"has_more={self.has_more})"
        )
