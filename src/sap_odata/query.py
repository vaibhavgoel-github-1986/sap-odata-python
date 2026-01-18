"""
Query Builder - Fluent interface for building OData queries.
"""

from typing import TYPE_CHECKING, Optional, List, Dict, Any, Union

if TYPE_CHECKING:
    from .service import ODataService


class QueryBuilder:
    """
    Fluent query builder for OData requests.
    
    Provides a chainable interface for building OData queries with
    support for filtering, selecting, expanding, pagination, and ordering.
    
    Example:
        >>> customers = (
        ...     service.entity("Customers")
        ...     .filter("Country eq 'US'")
        ...     .select("CustomerID", "Name", "Country")
        ...     .expand("Orders")
        ...     .top(10)
        ...     .orderby("Name asc")
        ...     .get()
        ... )
    """
    
    def __init__(self, service: "ODataService", entity_name: str) -> None:
        """Initialize query builder."""
        self._service = service
        self._entity_name = entity_name
        
        # Query options
        self._filter: Optional[str] = None
        self._select: List[str] = []
        self._expand: List[str] = []
        self._orderby: Optional[str] = None
        self._top: Optional[int] = None
        self._skip: Optional[int] = None
        self._count: bool = False
        self._search: Optional[str] = None
        self._custom_params: Dict[str, Any] = {}
    
    def filter(self, expression: str) -> "QueryBuilder":
        """
        Add a filter expression.
        
        Args:
            expression: OData filter expression
        
        Returns:
            Self for chaining
        
        Example:
            >>> .filter("Country eq 'US' and Active eq true")
            >>> .filter("Price gt 100")
            >>> .filter("contains(Name, 'Corp')")
        """
        self._filter = expression
        return self
    
    def select(self, *properties: str) -> "QueryBuilder":
        """
        Select specific properties.
        
        Args:
            *properties: Property names to select
        
        Returns:
            Self for chaining
        
        Example:
            >>> .select("CustomerID", "Name", "Country")
        """
        self._select.extend(properties)
        return self
    
    def expand(self, *navigations: str) -> "QueryBuilder":
        """
        Expand navigation properties.
        
        Args:
            *navigations: Navigation property names to expand
        
        Returns:
            Self for chaining
        
        Example:
            >>> .expand("Orders", "Addresses")
            >>> .expand("Orders($select=OrderID,Total)")
        """
        self._expand.extend(navigations)
        return self
    
    def orderby(self, expression: str) -> "QueryBuilder":
        """
        Order results.
        
        Args:
            expression: Order expression
        
        Returns:
            Self for chaining
        
        Example:
            >>> .orderby("Name asc")
            >>> .orderby("CreatedAt desc, Name asc")
        """
        self._orderby = expression
        return self
    
    def top(self, count: int) -> "QueryBuilder":
        """
        Limit number of results.
        
        Args:
            count: Maximum number of results
        
        Returns:
            Self for chaining
        
        Example:
            >>> .top(10)
        """
        self._top = count
        return self
    
    def skip(self, count: int) -> "QueryBuilder":
        """
        Skip a number of results (pagination).
        
        Args:
            count: Number of results to skip
        
        Returns:
            Self for chaining
        
        Example:
            >>> .skip(20).top(10)  # Page 3 with page size 10
        """
        self._skip = count
        return self
    
    def count(self, include: bool = True) -> "QueryBuilder":
        """
        Include count of total results.
        
        Args:
            include: Whether to include count
        
        Returns:
            Self for chaining
        
        Example:
            >>> .count()
        """
        self._count = include
        return self
    
    def search(self, term: str) -> "QueryBuilder":
        """
        Add free-text search (V4 only).
        
        Args:
            term: Search term
        
        Returns:
            Self for chaining
        
        Example:
            >>> .search("Corporation")
        """
        self._search = term
        return self
    
    def custom(self, key: str, value: Any) -> "QueryBuilder":
        """
        Add custom query parameter.
        
        Args:
            key: Parameter name
            value: Parameter value
        
        Returns:
            Self for chaining
        
        Example:
            >>> .custom("customParam", "value")
        """
        self._custom_params[key] = value
        return self
    
    def _build_params(self) -> Dict[str, Any]:
        """Build query parameters dictionary."""
        params: Dict[str, Any] = {}
        
        if self._filter:
            params["$filter"] = self._filter
        
        if self._select:
            params["$select"] = ",".join(self._select)
        
        if self._expand:
            params["$expand"] = ",".join(self._expand)
        
        if self._orderby:
            params["$orderby"] = self._orderby
        
        if self._top is not None:
            params["$top"] = self._top
        
        if self._skip is not None:
            params["$skip"] = self._skip
        
        if self._count:
            if self._service.version == "v4":
                params["$count"] = "true"
            else:  # v2
                params["$inlinecount"] = "allpages"
        
        if self._search:
            params["$search"] = self._search
        
        # Add custom parameters
        params.update(self._custom_params)
        
        return params
    
    def get(self) -> List[Dict[str, Any]]:
        """
        Execute query and return results as a list.
        
        Returns:
            List of entity dictionaries
        
        Example:
            >>> customers = service.entity("Customers").get()
            >>> for customer in customers:
            ...     print(customer["Name"])
        """
        from .response import EntityCollection
        
        params = self._build_params()
        result = self._service.execute_request(
            method="GET",
            entity_path=self._entity_name,
            params=params,
        )
        
        data = result.get("data", {})
        
        # Extract entities from response
        if "value" in data:
            return data["value"]
        elif isinstance(data, list):
            return data
        elif data:
            return [data]
        return []
    
    def get_single(self) -> Optional[Dict[str, Any]]:
        """
        Execute query and return single entity.
        
        Returns:
            Single entity dictionary or None
        
        Example:
            >>> customer = service.entity("Customers('CUST001')").get_single()
        """
        results = self.get()
        return results[0] if results else None
    
    def get_response(self) -> Dict[str, Any]:
        """
        Execute query and return full response including metadata.
        
        Returns:
            Full response dictionary with data and metadata
        
        Example:
            >>> response = service.entity("Customers").count().get_response()
            >>> total = response["data"].get("@odata.count")
        """
        params = self._build_params()
        return self._service.execute_request(
            method="GET",
            entity_path=self._entity_name,
            params=params,
        )
    
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new entity.
        
        Args:
            data: Entity data to create
        
        Returns:
            Created entity data
        
        Example:
            >>> new_customer = service.entity("Customers").create({
            ...     "CustomerID": "CUST001",
            ...     "Name": "New Customer",
            ...     "Country": "US"
            ... })
        """
        result = self._service.execute_request(
            method="POST",
            entity_path=self._entity_name,
            json_body=data,
        )
        return result.get("data", {})
    
    def update(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an entity (PATCH - partial update).
        
        Args:
            data: Entity data to update
        
        Returns:
            Updated entity data
        
        Example:
            >>> service.entity("Customers('CUST001')").update({
            ...     "Name": "Updated Name"
            ... })
        """
        result = self._service.execute_request(
            method="PATCH",
            entity_path=self._entity_name,
            json_body=data,
        )
        return result.get("data", {})
    
    def replace(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Replace an entity (PUT - full replacement).
        
        Args:
            data: Complete entity data
        
        Returns:
            Replaced entity data
        
        Example:
            >>> service.entity("Customers('CUST001')").replace({
            ...     "CustomerID": "CUST001",
            ...     "Name": "Full Replacement",
            ...     "Country": "CA",
            ...     "Active": True
            ... })
        """
        result = self._service.execute_request(
            method="PUT",
            entity_path=self._entity_name,
            json_body=data,
        )
        return result.get("data", {})
    
    def delete(self) -> bool:
        """
        Delete an entity.
        
        Returns:
            True if deletion was successful
        
        Example:
            >>> service.entity("Customers('CUST001')").delete()
        """
        result = self._service.execute_request(
            method="DELETE",
            entity_path=self._entity_name,
        )
        return result.get("status_code") in (200, 204)
    
    def __repr__(self) -> str:
        """String representation showing query details."""
        params = self._build_params()
        return f"QueryBuilder(entity='{self._entity_name}', params={params})"
