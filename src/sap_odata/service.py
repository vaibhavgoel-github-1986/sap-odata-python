"""
OData Service - Represents an OData service endpoint.
"""

from typing import TYPE_CHECKING, Optional, Literal, Dict, Any
from .query import QueryBuilder
from .metadata import Metadata
from .batch import BatchRequest

if TYPE_CHECKING:
    from .client import ODataClient


class ODataService:
    """
    Represents an OData service endpoint.
    
    This class provides methods to interact with a specific OData service,
    including querying entities, accessing metadata, and performing CRUD operations.
    
    Args:
        client: Parent ODataClient instance
        name: Service name
        namespace: Service namespace
        version: OData version ("v2" or "v4")
    
    Example:
        >>> service = client.service("ZSD_CUSTOMER_API", version="v4")
        >>> customers = service.entity("Customers").filter("Active eq true").get()
    """
    
    def __init__(
        self,
        client: "ODataClient",
        name: str,
        namespace: str,
        version: Literal["v2", "v4"],
    ) -> None:
        """Initialize OData Service."""
        self._client = client
        self.name = name
        self.namespace = namespace
        self.version = version
        
        # Build base path based on version
        if version == "v4":
            self._base_path = "/sap/opu/odata4/sap"
            # V4 URLs must be lowercase
            self._service_path = (
                f"{namespace.lower()}/srvd_a2x/sap/{name.lower()}/0001"
            )
        else:  # v2
            self._base_path = "/sap/opu/odata/sap"
            self._service_path = name
        
        self._full_path = f"{self._base_path}/{self._service_path}"
        
        # Cached metadata
        self._metadata: Optional[Metadata] = None
    
    @property
    def url(self) -> str:
        """Get the full service URL."""
        return f"{self._client.host}{self._full_path}"
    
    def entity(self, name: str) -> QueryBuilder:
        """
        Access an entity set for querying.
        
        Args:
            name: Entity set name or entity path with key
                  Examples: "Customers", "Customers('CUST001')", "Orders(123)/Items"
        
        Returns:
            QueryBuilder for constructing and executing queries
        
        Example:
            >>> # Get all customers
            >>> customers = service.entity("Customers").get()
            
            >>> # Get specific customer
            >>> customer = service.entity("Customers('CUST001')").get_single()
            
            >>> # Navigate to related entities
            >>> items = service.entity("Orders(123)/Items").get()
        """
        return QueryBuilder(service=self, entity_name=name)
    
    def metadata(self, force_refresh: bool = False) -> Metadata:
        """
        Get service metadata.
        
        Args:
            force_refresh: Force refresh metadata from server
        
        Returns:
            Metadata object with entity type definitions
        
        Example:
            >>> meta = service.metadata()
            >>> for entity_set in meta.entity_sets:
            ...     print(entity_set.name)
        """
        if self._metadata is None or force_refresh:
            self._metadata = self._fetch_metadata()
        return self._metadata
    
    def _fetch_metadata(self) -> Metadata:
        """Fetch and parse metadata from the service."""
        metadata_url = f"{self.url}/$metadata"
        
        headers = {
            "Accept": "application/xml",
            "Content-Type": "application/xml",
        }
        
        response = self._client.request(
            method="GET",
            url=metadata_url,
            headers=headers,
        )
        
        response.raise_for_status()
        return Metadata.from_xml(response.text, version=self.version)
    
    def batch(self) -> BatchRequest:
        """
        Create a batch request for executing multiple operations.
        
        Returns:
            BatchRequest object for adding operations
        
        Example:
            >>> with service.batch() as batch:
            ...     batch.get("Customers('CUST001')")
            ...     batch.create("Customers", {"Name": "New Customer"})
            >>> results = batch.execute()
        """
        return BatchRequest(service=self)
    
    def execute_request(
        self,
        method: str,
        entity_path: str,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute an HTTP request against the service.
        
        This is used internally by QueryBuilder and other components.
        
        Args:
            method: HTTP method
            entity_path: Entity path relative to service
            params: Query parameters
            json_body: JSON body for POST/PUT/PATCH
        
        Returns:
            Parsed response data
        """
        from .response import normalize_response
        from .exceptions import ODataError, ODataNotFoundError
        
        url = f"{self.url}/{entity_path}"
        
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        
        # Add CSRF token for write operations
        if method.upper() in ("POST", "PUT", "PATCH", "DELETE"):
            csrf_token = self._client.get_csrf_token(self._full_path)
            headers["X-CSRF-Token"] = csrf_token
        
        # Add $format=json for V2 GET requests
        request_params = params or {}
        if self.version == "v2" and method.upper() == "GET":
            if "$format" not in request_params:
                request_params["$format"] = "json"
        
        response = self._client.request(
            method=method,
            url=url,
            params=request_params,
            json=json_body,
            headers=headers,
        )
        
        # Handle errors
        if response.status_code == 404:
            raise ODataNotFoundError(f"Entity not found: {entity_path}")
        
        if not response.ok:
            error_detail = response.text[:500] if response.text else ""
            raise ODataError(
                f"HTTP {response.status_code}: {error_detail}",
                status_code=response.status_code,
            )
        
        # Parse and normalize response
        if response.text:
            data = response.json()
            if self._client.config.normalize_responses:
                data = normalize_response(data, self.version)
            return {
                "status_code": response.status_code,
                "data": data,
            }
        
        return {"status_code": response.status_code, "data": None}
    
    def __repr__(self) -> str:
        """String representation."""
        return f"ODataService(name='{self.name}', version='{self.version}')"
