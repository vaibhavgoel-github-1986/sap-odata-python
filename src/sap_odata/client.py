"""
OData Client - Main entry point for SAP OData operations.

Provides a unified interface for connecting to SAP systems and
interacting with OData V2 and V4 services.
"""

from typing import Optional, Literal, Dict, Any
import requests
from requests.auth import HTTPBasicAuth
import base64

from .config import ODataConfig
from .service import ODataService
from .exceptions import ODataConnectionError, ODataAuthenticationError


class ODataClient:
    """
    SAP OData Client supporting both V2 and V4 protocols.
    
    This is the main entry point for interacting with SAP OData services.
    It handles authentication, session management, and provides access to
    OData services.
    
    Args:
        host: SAP system URL (e.g., "https://sap-system.com")
        username: SAP username
        password: SAP password
        client: SAP client number (default: "100")
        config: Optional configuration object
    
    Example:
        >>> client = ODataClient(
        ...     host="https://sap-system.com",
        ...     username="myuser",
        ...     password="mypass",
        ...     client="100"
        ... )
        >>> service = client.service("ZSD_API", version="v4")
        >>> customers = service.entity("Customers").get()
    
    Attributes:
        host: The SAP system URL
        client: The SAP client number
        is_connected: Whether the client has an active session
    """
    
    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        client: str = "100",
        config: Optional[ODataConfig] = None,
    ) -> None:
        """Initialize OData Client with SAP credentials."""
        if not host:
            raise ValueError("host is required")
        if not username or not password:
            raise ValueError("username and password are required")
        
        # Normalize host URL
        self.host = host.rstrip("/")
        self.client = client
        self.config = config or ODataConfig()
        
        # Create session with authentication
        self._session = requests.Session()
        self._session.auth = HTTPBasicAuth(username, password)
        self._session.verify = self.config.verify_ssl
        
        # Store credentials for CSRF token refresh
        self._username = username
        self._password = password
        
        # CSRF token cache per service path
        self._csrf_tokens: Dict[str, str] = {}
        
        # Connection state
        self._is_connected = False
    
    @property
    def is_connected(self) -> bool:
        """Check if the client has verified connectivity."""
        return self._is_connected
    
    def connect(self) -> "ODataClient":
        """
        Verify connection to the SAP system.
        
        Makes a test request to verify credentials and connectivity.
        
        Returns:
            Self for method chaining
        
        Raises:
            ODataConnectionError: If unable to connect to the SAP system
            ODataAuthenticationError: If credentials are invalid
        """
        try:
            # Test connection with a simple metadata request
            test_url = f"{self.host}/sap/opu/odata/sap/"
            params = {"sap-client": self.client}
            
            response = self._session.get(
                test_url,
                params=params,
                timeout=self.config.timeout,
            )
            
            if response.status_code == 401:
                raise ODataAuthenticationError(
                    "Authentication failed. Please check your credentials."
                )
            
            self._is_connected = True
            return self
            
        except requests.exceptions.ConnectionError as e:
            raise ODataConnectionError(
                f"Unable to connect to {self.host}: {str(e)}"
            )
        except requests.exceptions.Timeout:
            raise ODataConnectionError(
                f"Connection to {self.host} timed out"
            )
    
    def service(
        self,
        name: str,
        namespace: Optional[str] = None,
        version: Literal["v2", "v4"] = "v4",
    ) -> ODataService:
        """
        Get an OData service instance.
        
        Args:
            name: Service name (e.g., "ZSD_CUSTOMER_API")
            namespace: Service namespace (required for V4, optional for V2)
            version: OData version ("v2" or "v4")
        
        Returns:
            ODataService instance for the specified service
        
        Example:
            >>> # V4 service (RAP/CAP)
            >>> service = client.service(
            ...     name="ZSD_CUSTOMER_API",
            ...     namespace="ZSB_CUSTOMER_API",
            ...     version="v4"
            ... )
            
            >>> # V2 service (Gateway)
            >>> service = client.service(name="ZSALESORDER_SRV", version="v2")
        """
        return ODataService(
            client=self,
            name=name,
            namespace=namespace or name,
            version=version,
        )
    
    def get_csrf_token(self, service_path: str) -> str:
        """
        Get CSRF token for a service path.
        
        Args:
            service_path: The OData service path
        
        Returns:
            CSRF token string
        
        Raises:
            ODataCSRFError: If unable to fetch CSRF token
        """
        from .exceptions import ODataCSRFError
        
        # Check cache first
        if service_path in self._csrf_tokens and not self.config.csrf_token_refresh:
            return self._csrf_tokens[service_path]
        
        # Fetch new token
        metadata_url = f"{self.host}{service_path}/$metadata"
        headers = {
            "X-CSRF-Token": "Fetch",
            "Accept": "application/xml",
        }
        params = {"sap-client": self.client}
        
        try:
            response = self._session.get(
                metadata_url,
                headers=headers,
                params=params,
                timeout=self.config.timeout,
            )
            
            csrf_token = response.headers.get("X-CSRF-Token")
            if not csrf_token or csrf_token == "Required":
                raise ODataCSRFError(
                    f"Failed to fetch CSRF token from {metadata_url}"
                )
            
            # Cache the token
            self._csrf_tokens[service_path] = csrf_token
            return csrf_token
            
        except requests.exceptions.RequestException as e:
            raise ODataCSRFError(f"Error fetching CSRF token: {str(e)}")
    
    def request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> requests.Response:
        """
        Make an HTTP request to the SAP system.
        
        This is a low-level method used by ODataService.
        
        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE)
            url: Full URL to request
            params: Query parameters
            json: JSON body for POST/PUT/PATCH
            headers: Additional headers
        
        Returns:
            Response object
        """
        request_params = params or {}
        if "sap-client" not in request_params:
            request_params["sap-client"] = self.client
        
        request_headers = headers or {}
        
        return self._session.request(
            method=method,
            url=url,
            params=request_params,
            json=json,
            headers=request_headers,
            timeout=self.config.timeout,
        )
    
    def close(self) -> None:
        """Close the client session."""
        self._session.close()
        self._is_connected = False
    
    def __enter__(self) -> "ODataClient":
        """Context manager entry."""
        return self.connect()
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()
    
    def __repr__(self) -> str:
        """String representation of the client."""
        return f"ODataClient(host='{self.host}', client='{self.client}')"
