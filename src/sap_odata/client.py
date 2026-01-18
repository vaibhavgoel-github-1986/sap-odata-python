"""
SAP OData Client - Main client class with generic function approach.

This module provides the SAPODataClient class which offers a unified,
AI-friendly interface to OData V2 and V4 services.

Works with:
- SAP systems (S/4HANA, BTP, Gateway)
- Public OData services (Northwind, etc.)
- Any OData V2/V4 compliant service
"""

import requests
from requests.auth import HTTPBasicAuth
from typing import Optional, Literal, Dict, Any, Union
from urllib.parse import urljoin
import logging

from .exceptions import (
    SAPConnectionError,
    SAPAuthenticationError,
    SAPServiceError,
    SAPCSRFTokenError,
    SAPMetadataError,
)
from .response import ODataResponse
from .metadata import MetadataParser

logger = logging.getLogger(__name__)


class SAPODataClient:
    """
    OData Client with unified generic function approach.
    
    Supports both OData V2 and V4 protocols through a single generic function call,
    making it ideal for AI/LLM integration.
    
    Works with SAP systems and any OData-compliant service.
    
    Attributes:
        host: Base URL (e.g., 'https://services.odata.org')
        client: SAP client number (optional, for SAP systems only)
        session: Authenticated requests session
        is_sap: Whether connected to an SAP system
    
    Example:
        >>> # Public OData service
        >>> client = SAPODataClient(
        ...     host="https://services.odata.org",
        ...     username="",
        ...     password=""
        ... )
        >>> response = client.call_odata(
        ...     http_method="GET",
        ...     service_name="V4/Northwind/Northwind.svc",
        ...     entity_name="Products",
        ...     odata_version="v4"
        ... )
        >>> 
        >>> # SAP system
        >>> client = SAPODataClient(
        ...     host="https://sap-system.company.com",
        ...     username="user",
        ...     password="pass",
        ...     client="100"
        ... )
        >>> response = client.call_odata(
        ...     http_method="GET",
        ...     service_name="ZSD_CUSTOMER_API",
        ...     entity_name="Customers",
        ...     odata_version="v4"
        ... )
    """
    
    # SAP-specific OData URL patterns
    SAP_V2_BASE_PATH = "/sap/opu/odata/sap"
    SAP_V4_BASE_PATH = "/sap/opu/odata4/sap"
    
    def __init__(
        self,
        host: str,
        username: str = "",
        password: str = "",
        client: str = "",
        verify_ssl: bool = True,
        timeout: int = 120,
        is_sap: Optional[bool] = None,
    ):
        """
        Initialize OData Client.
        
        Args:
            host: OData service base URL.
                  Examples: 'https://services.odata.org',
                           'https://sap-dev.company.com:8000'
            username: Username for authentication (optional for public services)
            password: Password for authentication (optional for public services)
            client: SAP client number (optional, for SAP systems only).
                    Common values: '100', '110' (dev), '300' (QA)
            verify_ssl: Whether to verify SSL certificates (default: True)
            timeout: Request timeout in seconds (default: 120)
            is_sap: Force SAP mode (auto-detected if None)
        
        Raises:
            SAPConnectionError: If unable to connect
            SAPAuthenticationError: If credentials are invalid
        """
        self.host = host.rstrip('/')
        self.client = client
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        
        # Auto-detect SAP system
        if is_sap is None:
            self.is_sap = bool(client) or 'sap' in host.lower()
        else:
            self.is_sap = is_sap
        
        # Create session
        self.session = requests.Session()
        if username and password:
            self.session.auth = HTTPBasicAuth(username, password)
        self.session.verify = verify_ssl
        
        # CSRF token cache
        self._csrf_tokens: Dict[str, str] = {}
        
        # Skip validation for public services
        if username and password:
            self._validate_connection()
        
        logger.info(f"OData Client initialized for {host}")
    
    def _validate_connection(self) -> None:
        """Validate connection to the OData service."""
        try:
            # For SAP systems, try ADT discovery
            if self.is_sap:
                params = {"sap-client": self.client} if self.client else {}
                response = self.session.get(
                    f"{self.host}/sap/bc/adt/core/discovery",
                    params=params,
                    timeout=self.timeout,
                )
                
                if response.status_code == 401:
                    raise SAPAuthenticationError("Invalid credentials")
                elif response.status_code >= 400:
                    # Try OData root
                    response = self.session.get(
                        f"{self.host}/sap/opu/odata/sap/",
                        params=params,
                        timeout=self.timeout,
                    )
                    if response.status_code == 401:
                        raise SAPAuthenticationError("Invalid credentials")
            else:
                # For non-SAP, just check the host is reachable
                response = self.session.head(self.host, timeout=self.timeout)
                if response.status_code == 401:
                    raise SAPAuthenticationError("Invalid credentials")
                    
        except requests.exceptions.ConnectionError as e:
            raise SAPConnectionError(f"Cannot connect to OData service: {e}")
        except requests.exceptions.Timeout:
            raise SAPConnectionError("Connection timeout")
    
    def call_odata(
        self,
        http_method: str,
        service_name: str,
        entity_name: str,
        service_namespace: Optional[str] = None,
        odata_version: Literal["v2", "v4"] = "v4",
        query_parameters: Optional[Dict[str, Any]] = None,
        request_body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> ODataResponse:
        """
        Call any SAP OData service with a single generic function.
        
        This is the primary method for all OData operations. It provides a unified
        interface for both V2 (Gateway) and V4 (RAP/CAP) services.
        
        Args:
            http_method: HTTP method to use.
                        - 'GET': Retrieve data (read operations)
                        - 'POST': Create new records
                        - 'PUT': Replace entire record (full update)
                        - 'PATCH': Update specific fields (partial update)
                        - 'DELETE': Remove records
                        - 'HEAD', 'OPTIONS': Metadata operations
            
            service_name: SAP OData service name.
                         Examples: 'ZSD_CUSTOMER_API', 'SALESORDER_SRV',
                                  'API_BUSINESS_PARTNER'
            
            entity_name: Entity name or path with optional keys.
                        Examples:
                        - 'Customers' - Entity set
                        - 'Customers('CUST001')' - Single entity by key
                        - 'Orders('12345')/Items' - Navigation property
                        - 'Products('MAT123')/to_Details' - Deep navigation
            
            service_namespace: Service namespace (required for V4, optional for V2).
                              Usually same as service_name or starts with 'ZSB_'.
                              If not provided, defaults to service_name for V4.
            
            odata_version: OData protocol version.
                          - 'v2': SAP Gateway services (legacy)
                          - 'v4': SAP RAP/CAP services (modern)
            
            query_parameters: Query parameters as dictionary.
                             Common parameters:
                             - '$filter': 'Price gt 100 and Status eq "A"'
                             - '$select': 'CustomerID,Name,Country'
                             - '$expand': 'Orders,Addresses'
                             - '$top': 10 (limit results)
                             - '$skip': 20 (pagination offset)
                             - '$orderby': 'Name asc, CreatedAt desc'
                             - '$count': True (include count)
                             - '$search': 'keyword' (full-text search)
            
            request_body: Request body for POST/PUT/PATCH operations.
                         Should be a dictionary matching entity structure.
                         Example: {'CustomerID': 'CUST001', 'Name': 'ACME Corp'}
            
            headers: Additional HTTP headers (optional).
                    Default headers (Accept, Content-Type, CSRF) are set automatically.
        
        Returns:
            ODataResponse: Response object containing:
                - status_code: HTTP status code
                - data: Normalized response data (always has 'value' array)
                - raw_response: Original response for debugging
                - count: Record count if $count was requested
                - next_link: Pagination link if more data available
        
        Raises:
            SAPServiceError: If the OData service returns an error
            SAPCSRFTokenError: If CSRF token fetch fails for write operations
        
        Examples:
            >>> # GET: Retrieve all customers
            >>> response = client.call_odata(
            ...     http_method="GET",
            ...     service_name="ZSD_CUSTOMER_API",
            ...     entity_name="Customers",
            ...     odata_version="v4",
            ...     query_parameters={"$top": 10, "$select": "CustomerID,Name"}
            ... )
            >>> print(response.data)
            
            >>> # GET: Filter customers by country
            >>> response = client.call_odata(
            ...     http_method="GET",
            ...     service_name="ZSD_CUSTOMER_API",
            ...     entity_name="Customers",
            ...     odata_version="v2",
            ...     query_parameters={"$filter": "Country eq 'US' and Active eq true"}
            ... )
            
            >>> # GET: Single entity by key
            >>> response = client.call_odata(
            ...     http_method="GET",
            ...     service_name="API_BUSINESS_PARTNER",
            ...     entity_name="A_BusinessPartner('1000001')",
            ...     odata_version="v2"
            ... )
            
            >>> # POST: Create new customer
            >>> response = client.call_odata(
            ...     http_method="POST",
            ...     service_name="ZSD_CUSTOMER_API",
            ...     entity_name="Customers",
            ...     odata_version="v4",
            ...     request_body={
            ...         "CustomerID": "CUST123",
            ...         "Name": "ACME Corporation",
            ...         "Country": "US",
            ...         "Active": True
            ...     }
            ... )
            
            >>> # PATCH: Update specific fields
            >>> response = client.call_odata(
            ...     http_method="PATCH",
            ...     service_name="ZSD_CUSTOMER_API",
            ...     entity_name="Customers('CUST123')",
            ...     odata_version="v4",
            ...     request_body={"Status": "Inactive"}
            ... )
            
            >>> # DELETE: Remove entity
            >>> response = client.call_odata(
            ...     http_method="DELETE",
            ...     service_name="ZSD_CUSTOMER_API",
            ...     entity_name="Customers('CUST123')",
            ...     odata_version="v4"
            ... )
        """
        # Validate inputs
        http_method = http_method.upper()
        if http_method not in ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]:
            raise ValueError(f"Invalid HTTP method: {http_method}")
        
        if not service_name:
            raise ValueError("service_name is required")
        
        if not entity_name:
            raise ValueError("entity_name is required")
        
        # Build service URL based on OData version
        url = self._build_service_url(
            service_name=service_name,
            entity_name=entity_name,
            service_namespace=service_namespace,
            odata_version=odata_version,
        )
        
        # Prepare query parameters
        params = self._prepare_query_params(
            query_parameters=query_parameters,
            odata_version=odata_version,
            http_method=http_method,
        )
        
        # Prepare headers
        request_headers = self._prepare_headers(
            http_method=http_method,
            odata_version=odata_version,
            additional_headers=headers,
            service_name=service_name,
            service_namespace=service_namespace,
        )
        
        # Log the request
        logger.info(
            f"OData {odata_version} {http_method} request",
            extra={
                "service": service_name,
                "entity": entity_name,
                "url": url,
            }
        )
        
        try:
            # Make the request
            response = self.session.request(
                method=http_method,
                url=url,
                params=params,
                json=request_body if request_body else None,
                headers=request_headers,
                timeout=self.timeout,
            )
            
            # Handle response
            return self._process_response(response, odata_version)
            
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else 0
            error_body = e.response.text[:1000] if e.response else str(e)
            raise SAPServiceError(
                f"OData service error (HTTP {status_code}): {error_body}",
                status_code=status_code,
                response_body=error_body,
            )
        except requests.exceptions.RequestException as e:
            raise SAPServiceError(f"Request failed: {e}")
    
    def get_metadata(
        self,
        service_name: str,
        service_namespace: Optional[str] = None,
        odata_version: Literal["v2", "v4"] = "v4",
        parse: bool = False,
    ) -> Union[str, MetadataParser]:
        """
        Get OData service metadata.
        
        Args:
            service_name: OData service name or path
            service_namespace: Service namespace (for SAP V4 services)
            odata_version: 'v2' or 'v4'
            parse: If True, returns parsed MetadataParser object.
                   If False (default), returns raw XML string.
        
        Returns:
            Raw metadata XML string, or MetadataParser object if parse=True
        
        Raises:
            SAPMetadataError: If metadata fetch fails
        
        Example:
            >>> # Public OData service
            >>> xml = client.get_metadata("V4/Northwind/Northwind.svc", odata_version="v4")
            >>> 
            >>> # SAP service
            >>> metadata = client.get_metadata("ZSD_CUSTOMER_API", odata_version="v4", parse=True)
        """
        # Build metadata URL
        url = self._build_metadata_url(service_name, service_namespace, odata_version)
        
        params = {}
        if self.is_sap and self.client:
            params["sap-client"] = self.client
        
        headers = {"Accept": "application/xml"}
        
        try:
            response = self.session.get(
                url=url,
                params=params,
                headers=headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            
            xml_content = response.text
            
            if not xml_content.strip():
                raise SAPMetadataError("Empty metadata response")
            
            if parse:
                return MetadataParser(xml_content)
            
            return xml_content
            
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else 0
            raise SAPMetadataError(
                f"Failed to fetch metadata (HTTP {status_code})",
                status_code=status_code,
            )
    
    def _build_metadata_url(
        self,
        service_name: str,
        service_namespace: Optional[str],
        odata_version: str,
    ) -> str:
        """Build metadata URL based on service type."""
        if self.is_sap:
            # SAP-specific URL patterns
            if odata_version == "v4":
                namespace = (service_namespace or service_name).lower()
                service_path = f"{namespace}/srvd_a2x/sap/{service_name.lower()}/0001"
                return f"{self.host}{self.SAP_V4_BASE_PATH}/{service_path}/$metadata"
            else:
                return f"{self.host}{self.SAP_V2_BASE_PATH}/{service_name}/$metadata"
        else:
            # Generic OData service - service_name is the full path
            if service_name.startswith('/'):
                return f"{self.host}{service_name}/$metadata"
            return f"{self.host}/{service_name}/$metadata"
    
    def _build_service_url(
        self,
        service_name: str,
        entity_name: str,
        service_namespace: Optional[str],
        odata_version: str,
    ) -> str:
        """Build the full service URL based on service type and OData version."""
        if self.is_sap:
            # SAP-specific URL patterns
            if odata_version == "v4":
                namespace = (service_namespace or service_name).lower()
                service_path = f"{namespace}/srvd_a2x/sap/{service_name.lower()}/0001"
                return f"{self.host}{self.SAP_V4_BASE_PATH}/{service_path}/{entity_name}"
            else:
                return f"{self.host}{self.SAP_V2_BASE_PATH}/{service_name}/{entity_name}"
        else:
            # Generic OData service - service_name is the full path
            if service_name.startswith('/'):
                return f"{self.host}{service_name}/{entity_name}"
            return f"{self.host}/{service_name}/{entity_name}"
    
    def _prepare_query_params(
        self,
        query_parameters: Optional[Dict[str, Any]],
        odata_version: str,
        http_method: str,
    ) -> Dict[str, Any]:
        """Prepare query parameters for the request."""
        params = dict(query_parameters) if query_parameters else {}
        
        # Add sap-client for SAP systems on GET requests
        if self.is_sap and self.client and http_method == "GET" and "sap-client" not in params:
            params["sap-client"] = self.client
        
        # For V2 GET requests, ensure JSON format
        if odata_version == "v2" and http_method == "GET" and "$format" not in params:
            params["$format"] = "json"
        
        return params
    
    def _prepare_headers(
        self,
        http_method: str,
        odata_version: str,
        additional_headers: Optional[Dict[str, str]],
        service_name: str,
        service_namespace: Optional[str],
    ) -> Dict[str, str]:
        """Prepare HTTP headers including CSRF token for write operations."""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        
        # Add CSRF token for state-changing operations (only for SAP systems)
        if http_method in ["POST", "PUT", "PATCH", "DELETE"] and self.is_sap:
            try:
                csrf_token = self._get_csrf_token(service_name, service_namespace, odata_version)
                headers["X-CSRF-Token"] = csrf_token
            except SAPCSRFTokenError:
                # Non-SAP services may not require CSRF
                pass
        
        # Merge additional headers
        if additional_headers:
            headers.update(additional_headers)
        
        return headers
    
    def _get_csrf_token(
        self,
        service_name: str,
        service_namespace: Optional[str],
        odata_version: str,
    ) -> str:
        """Fetch CSRF token for write operations (SAP systems only)."""
        if not self.is_sap:
            raise SAPCSRFTokenError("CSRF tokens only required for SAP systems")
        
        # Build cache key
        cache_key = f"{odata_version}:{service_name}:{service_namespace or ''}"
        
        # Check cache first
        if cache_key in self._csrf_tokens:
            return self._csrf_tokens[cache_key]
        
        # Build token fetch URL (SAP-specific)
        if odata_version == "v4":
            namespace = (service_namespace or service_name).lower()
            service_path = f"{namespace}/srvd_a2x/sap/{service_name.lower()}/0001"
            url = f"{self.host}{self.SAP_V4_BASE_PATH}/{service_path}/"
        else:
            url = f"{self.host}{self.SAP_V2_BASE_PATH}/{service_name}/"
        
        try:
            params = {}
            if self.client:
                params["sap-client"] = self.client
                
            response = self.session.get(
                url=url,
                params=params,
                headers={"X-CSRF-Token": "Fetch"},
                timeout=self.timeout,
            )
            
            token = response.headers.get("X-CSRF-Token")
            if not token or token == "Required":
                raise SAPCSRFTokenError("Failed to fetch CSRF token")
            
            # Cache the token
            self._csrf_tokens[cache_key] = token
            return token
            
        except requests.exceptions.RequestException as e:
            raise SAPCSRFTokenError(f"CSRF token fetch failed: {e}")
    
    def _process_response(
        self,
        response: requests.Response,
        odata_version: str,
    ) -> ODataResponse:
        """Process and normalize the OData response."""
        response.raise_for_status()
        
        # Handle empty responses (DELETE, etc.)
        if response.status_code == 204 or not response.text.strip():
            return ODataResponse(
                status_code=response.status_code,
                data={"value": []},
                raw_response=None,
            )
        
        try:
            data = response.json()
        except ValueError:
            # Non-JSON response
            return ODataResponse(
                status_code=response.status_code,
                data={"value": [], "raw": response.text},
                raw_response=response.text,
            )
        
        # Normalize V2 response format to match V4 structure
        normalized = self._normalize_response(data, odata_version)
        
        return ODataResponse(
            status_code=response.status_code,
            data=normalized,
            raw_response=data,
            count=normalized.get("@odata.count"),
            next_link=normalized.get("@odata.nextLink"),
        )
    
    def _normalize_response(
        self,
        data: Dict[str, Any],
        odata_version: str,
    ) -> Dict[str, Any]:
        """
        Normalize response to consistent structure.
        
        Both V2 and V4 responses are normalized to:
        {
            "value": [...],  # Array of results
            "@odata.count": 123,  # Optional count
            "@odata.nextLink": "...",  # Optional pagination
        }
        """
        if odata_version == "v2":
            # V2 format options:
            # 1. {"d": {"results": [...], "__count": "10", "__next": "..."}}
            # 2. {"d": {...}} - single entity
            # 3. {"value": [...]} - some V2 services use V4-like format
            if "d" in data:
                d = data["d"]
                if isinstance(d, dict):
                    if "results" in d:
                        normalized = {"value": d["results"]}
                        if "__count" in d:
                            normalized["@odata.count"] = int(d["__count"])
                        if "__next" in d:
                            normalized["@odata.nextLink"] = d["__next"]
                        return normalized
                    else:
                        # Single entity response
                        return {"value": [d]}
                elif isinstance(d, list):
                    # Some services return {"d": [...]}
                    return {"value": d}
            elif "value" in data:
                # V4-like format in V2 service
                return data
            return {"value": [data] if data else []}
        else:
            # V4 format is already normalized
            if "value" not in data:
                # Single entity or special response
                return {"value": [data] if data else []}
            return data
    
    def clear_csrf_cache(self) -> None:
        """Clear cached CSRF tokens."""
        self._csrf_tokens.clear()
    
    def close(self) -> None:
        """Close the session and release resources."""
        self.session.close()
        self._csrf_tokens.clear()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False
    
    def __repr__(self) -> str:
        return f"SAPODataClient(host='{self.host}', client='{self.client}')"


# Convenience function for one-off calls
def call_odata(
    host: str,
    username: str,
    password: str,
    http_method: str,
    service_name: str,
    entity_name: str,
    client: str = "100",
    service_namespace: Optional[str] = None,
    odata_version: Literal["v2", "v4"] = "v4",
    query_parameters: Optional[Dict[str, Any]] = None,
    request_body: Optional[Dict[str, Any]] = None,
) -> ODataResponse:
    """
    Convenience function for one-off OData calls without creating a client.
    
    This is the simplest way to call an SAP OData service. Creates a temporary
    client, makes the call, and cleans up automatically.
    
    Args:
        host: SAP system URL
        username: SAP username
        password: SAP password
        http_method: HTTP method (GET, POST, PUT, PATCH, DELETE)
        service_name: OData service name
        entity_name: Entity name or path
        client: SAP client number (default: '100')
        service_namespace: Service namespace (for V4)
        odata_version: 'v2' or 'v4' (default: 'v4')
        query_parameters: Query parameters dict
        request_body: Request body for write operations
    
    Returns:
        ODataResponse with the result
    
    Example:
        >>> from sap_odata import call_odata
        >>> 
        >>> response = call_odata(
        ...     host="https://sap-system.company.com",
        ...     username="user",
        ...     password="pass",
        ...     http_method="GET",
        ...     service_name="ZSD_CUSTOMER_API",
        ...     entity_name="Customers",
        ...     odata_version="v4",
        ...     query_parameters={"$filter": "Country eq 'US'"}
        ... )
    """
    with SAPODataClient(host, username, password, client) as client_instance:
        return client_instance.call_odata(
            http_method=http_method,
            service_name=service_name,
            entity_name=entity_name,
            service_namespace=service_namespace,
            odata_version=odata_version,
            query_parameters=query_parameters,
            request_body=request_body,
        )
