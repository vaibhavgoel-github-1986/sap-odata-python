"""
OData Client - Simple client for OData V2 and V4 services.
"""

import requests
from requests.auth import HTTPBasicAuth
from typing import Optional, Dict, Any, Literal

from .exceptions import ODataError, ODataConnectionError, ODataAuthError


class ODataClient:
    """
    Simple OData client supporting V2 and V4 protocols.

    Example:
        >>> client = ODataClient("https://services.odata.org")
        >>> data = client.get("V4/Northwind/Northwind.svc", "Products", top=5)
        >>> print(data["value"])
    """

    # SAP URL patterns
    SAP_V2_PATH = "/sap/opu/odata/sap"
    SAP_V4_PATH = "/sap/opu/odata4/sap"

    def __init__(
        self,
        host: str,
        username: str = "",
        password: str = "",
        client: str = "",
        verify_ssl: bool = True,
        timeout: int = 60,
    ):
        """
        Initialize OData client.

        Args:
            host: Base URL (e.g., 'https://services.odata.org')
            username: Username for auth (optional)
            password: Password for auth (optional)
            client: SAP client number (optional)
            verify_ssl: Verify SSL certificates
            timeout: Request timeout in seconds
        """
        self.host = host.rstrip("/")
        self.client = client
        self.timeout = timeout
        self.is_sap = bool(client) or "sap" in host.lower()

        self.session = requests.Session()
        self.session.verify = verify_ssl
        if username and password:
            self.session.auth = HTTPBasicAuth(username, password)

        self._csrf_token: Optional[str] = None

    def get(
        self,
        service: str,
        entity: str,
        version: Literal["v2", "v4"] = "v4",
        namespace: str = "",
        **query_params,
    ) -> Dict[str, Any]:
        """
        GET request to retrieve data.

        Args:
            service: Service name or path
            entity: Entity name (e.g., 'Products', 'Products(1)')
            version: OData version ('v2' or 'v4')
            namespace: Service namespace (for SAP V4)
            **query_params: Query params like top=10, filter="Price gt 100"

        Returns:
            Response data as dict with 'value' key containing results
        """
        return self._request("GET", service, entity, version, namespace, query_params)

    def post(
        self,
        service: str,
        entity: str,
        data: Dict[str, Any],
        version: Literal["v2", "v4"] = "v4",
        namespace: str = "",
    ) -> Dict[str, Any]:
        """POST request to create data."""
        return self._request("POST", service, entity, version, namespace, body=data)

    def patch(
        self,
        service: str,
        entity: str,
        data: Dict[str, Any],
        version: Literal["v2", "v4"] = "v4",
        namespace: str = "",
    ) -> Dict[str, Any]:
        """PATCH request to update data."""
        return self._request("PATCH", service, entity, version, namespace, body=data)

    def delete(
        self,
        service: str,
        entity: str,
        version: Literal["v2", "v4"] = "v4",
        namespace: str = "",
    ) -> Dict[str, Any]:
        """DELETE request to remove data."""
        return self._request("DELETE", service, entity, version, namespace)

    def metadata(
        self, service: str, version: Literal["v2", "v4"] = "v4", namespace: str = ""
    ) -> str:
        """Get service metadata XML."""
        url = self._build_url(service, "$metadata", version, namespace)
        response = self.session.get(
            url, params=self._get_params({}), headers={"Accept": "application/xml"}, timeout=self.timeout
        )
        response.raise_for_status()
        return response.text

    def _request(
        self,
        method: str,
        service: str,
        entity: str,
        version: str,
        namespace: str,
        query_params: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make HTTP request."""
        url = self._build_url(service, entity, version, namespace)
        params = self._get_params(query_params or {}, version, method)
        headers = self._get_headers(method, service, version, namespace)

        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=body,
                headers=headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.exceptions.ConnectionError as e:
            raise ODataConnectionError(f"Connection failed: {e}")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise ODataAuthError("Authentication failed")
            raise ODataError(f"HTTP {e.response.status_code}: {e.response.text[:200]}")

        return self._normalize_response(response, version)

    def _build_url(self, service: str, entity: str, version: str, namespace: str) -> str:
        """Build the service URL."""
        if self.is_sap:
            if version == "v4":
                ns = (namespace or service).lower()
                path = f"{ns}/srvd_a2x/sap/{service.lower()}/0001"
                return f"{self.host}{self.SAP_V4_PATH}/{path}/{entity}"
            return f"{self.host}{self.SAP_V2_PATH}/{service}/{entity}"

        # Generic OData service
        service = service.lstrip("/")
        return f"{self.host}/{service}/{entity}"

    def _get_params(
        self, params: Dict[str, Any], version: str = "v4", method: str = "GET"
    ) -> Dict[str, Any]:
        """Build query parameters."""
        result = {}

        # Convert shorthand to OData format
        mapping = {"top": "$top", "skip": "$skip", "filter": "$filter", 
                   "select": "$select", "expand": "$expand", "orderby": "$orderby"}
        for key, value in params.items():
            result[mapping.get(key, key)] = value

        # SAP client
        if self.is_sap and self.client and method == "GET":
            result["sap-client"] = self.client

        # V2 needs explicit JSON format
        if version == "v2" and method == "GET" and "$format" not in result:
            result["$format"] = "json"

        return result

    def _get_headers(
        self, method: str, service: str, version: str, namespace: str
    ) -> Dict[str, str]:
        """Build request headers."""
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        # CSRF token for write operations (SAP only)
        if method in ("POST", "PATCH", "PUT", "DELETE") and self.is_sap:
            if not self._csrf_token:
                self._fetch_csrf_token(service, version, namespace)
            if self._csrf_token:
                headers["X-CSRF-Token"] = self._csrf_token

        return headers

    def _fetch_csrf_token(self, service: str, version: str, namespace: str) -> None:
        """Fetch CSRF token from service."""
        url = self._build_url(service, "", version, namespace)
        try:
            response = self.session.get(
                url,
                params={"sap-client": self.client} if self.client else {},
                headers={"X-CSRF-Token": "Fetch"},
                timeout=self.timeout,
            )
            token = response.headers.get("X-CSRF-Token")
            if token and token != "Required":
                self._csrf_token = token
        except Exception:
            pass  # CSRF not required for all services

    def _normalize_response(
        self, response: requests.Response, version: str
    ) -> Dict[str, Any]:
        """Normalize response to consistent format."""
        if response.status_code == 204 or not response.text.strip():
            return {"value": []}

        try:
            data = response.json()
        except ValueError:
            return {"value": [], "raw": response.text}

        # V2 format: {"d": {"results": [...]}} or {"d": {...}}
        if version == "v2" and "d" in data:
            d = data["d"]
            if isinstance(d, dict) and "results" in d:
                return {"value": d["results"]}
            if isinstance(d, list):
                return {"value": d}
            return {"value": [d] if d else []}

        # V4 format or already normalized
        if "value" not in data:
            return {"value": [data] if data else []}
        return data

    def close(self) -> None:
        """Close the session."""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
