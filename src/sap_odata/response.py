"""
Response - Response handling and normalization.
"""

from typing import Dict, Any, List, Optional, Iterator, Literal
from dataclasses import dataclass


def normalize_response(data: Dict[str, Any], version: Literal["v2", "v4"]) -> Dict[str, Any]:
    """
    Normalize OData response to a consistent format.
    
    V2 responses are transformed to match V4 structure for consistency.
    
    Args:
        data: Raw response data
        version: OData version
    
    Returns:
        Normalized response dictionary
    """
    if version == "v2" and "d" in data:
        d_data = data["d"]
        
        # Handle collection response
        if "results" in d_data:
            normalized = {
                "value": d_data["results"],
            }
            
            # Convert __count to @odata.count
            if "__count" in d_data:
                normalized["@odata.count"] = int(d_data["__count"])
            
            # Convert __next to @odata.nextLink
            if "__next" in d_data:
                normalized["@odata.nextLink"] = d_data["__next"]
            
            return normalized
        else:
            # Single entity response
            return {"value": [d_data]}
    
    return data


@dataclass
class ODataResponse:
    """
    Represents an OData API response.
    
    Provides convenience methods for accessing response data and metadata.
    
    Attributes:
        status_code: HTTP status code
        data: Response data
        raw_data: Original raw response data
    """
    status_code: int
    data: Dict[str, Any]
    raw_data: Optional[Dict[str, Any]] = None
    
    @property
    def value(self) -> List[Dict[str, Any]]:
        """Get the value array (entities)."""
        return self.data.get("value", [])
    
    @property
    def count(self) -> Optional[int]:
        """Get the total count if available."""
        return self.data.get("@odata.count")
    
    @property
    def next_link(self) -> Optional[str]:
        """Get the next page link if available."""
        return self.data.get("@odata.nextLink")
    
    @property
    def is_success(self) -> bool:
        """Check if the response was successful."""
        return 200 <= self.status_code < 300
    
    def __iter__(self) -> Iterator[Dict[str, Any]]:
        """Iterate over entities in the response."""
        return iter(self.value)
    
    def __len__(self) -> int:
        """Get number of entities in the response."""
        return len(self.value)
    
    def __bool__(self) -> bool:
        """Check if response has data."""
        return self.is_success and len(self.value) > 0


class EntityCollection:
    """
    Collection of entities with iteration and pagination support.
    
    Example:
        >>> customers = service.entity("Customers").get()
        >>> for customer in customers:
        ...     print(customer.Name)
    """
    
    def __init__(
        self,
        entities: List[Dict[str, Any]],
        count: Optional[int] = None,
        next_link: Optional[str] = None,
    ) -> None:
        """Initialize entity collection."""
        self._entities = entities
        self._count = count
        self._next_link = next_link
    
    @property
    def count(self) -> Optional[int]:
        """Total count of entities (if requested)."""
        return self._count
    
    @property
    def next_link(self) -> Optional[str]:
        """Link to next page of results."""
        return self._next_link
    
    @property
    def has_more(self) -> bool:
        """Check if there are more results."""
        return self._next_link is not None
    
    def __iter__(self) -> Iterator[Dict[str, Any]]:
        """Iterate over entities."""
        return iter(self._entities)
    
    def __len__(self) -> int:
        """Get number of entities in collection."""
        return len(self._entities)
    
    def __getitem__(self, index: int) -> Dict[str, Any]:
        """Get entity by index."""
        return self._entities[index]
    
    def first(self) -> Optional[Dict[str, Any]]:
        """Get first entity or None."""
        return self._entities[0] if self._entities else None
    
    def to_list(self) -> List[Dict[str, Any]]:
        """Convert to list."""
        return list(self._entities)


class Entity:
    """
    Wrapper for a single entity with attribute access.
    
    Example:
        >>> customer = Entity({"CustomerID": "CUST001", "Name": "ACME"})
        >>> print(customer.Name)  # Attribute access
        >>> print(customer["CustomerID"])  # Dict access
    """
    
    def __init__(self, data: Dict[str, Any]) -> None:
        """Initialize entity wrapper."""
        self._data = data
    
    def __getattr__(self, name: str) -> Any:
        """Get attribute by name."""
        if name.startswith("_"):
            raise AttributeError(name)
        try:
            return self._data[name]
        except KeyError:
            raise AttributeError(f"Entity has no property '{name}'")
    
    def __getitem__(self, key: str) -> Any:
        """Get property by key."""
        return self._data[key]
    
    def __contains__(self, key: str) -> bool:
        """Check if property exists."""
        return key in self._data
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get property with default."""
        return self._data.get(key, default)
    
    def keys(self):
        """Get property names."""
        return self._data.keys()
    
    def values(self):
        """Get property values."""
        return self._data.values()
    
    def items(self):
        """Get property items."""
        return self._data.items()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return dict(self._data)
    
    def __repr__(self) -> str:
        """String representation."""
        return f"Entity({self._data})"
