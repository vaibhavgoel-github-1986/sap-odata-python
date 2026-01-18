"""
SAP OData Python Client Library

A unified, AI-friendly Python library for SAP OData V2 and V4 services.
Designed with a generic function approach optimized for LLM/AI tool calling.

Design Philosophy:
    This library uses a single generic function approach (call_odata) instead of
    fluent/builder patterns. This design is intentional for:
    
    1. LLM/AI Friendliness - Easy for AI to generate single function calls
    2. MCP/Tool Calling - Perfect for Model Context Protocol tools
    3. Explicit Parameters - All parameters visible in one call
    4. Flexibility - Any HTTP method, any entity, any query
    5. Easy Serialization - Just JSON parameters

Example:
    >>> from sap_odata import SAPODataClient
    >>> 
    >>> # Create client
    >>> client = SAPODataClient(
    ...     host="https://sap-system.company.com",
    ...     username="user",
    ...     password="pass",
    ...     client="100"
    ... )
    >>> 
    >>> # GET: Retrieve customers with filter
    >>> response = client.call_odata(
    ...     http_method="GET",
    ...     service_name="ZSD_CUSTOMER_API",
    ...     entity_name="Customers",
    ...     odata_version="v4",
    ...     query_parameters={"$filter": "Country eq 'US'", "$top": 10}
    ... )
    >>> 
    >>> # POST: Create new record
    >>> response = client.call_odata(
    ...     http_method="POST",
    ...     service_name="ZSD_CUSTOMER_API",
    ...     entity_name="Customers",
    ...     odata_version="v4",
    ...     request_body={"CustomerID": "CUST001", "Name": "ACME Corp"}
    ... )
    >>> 
    >>> # Get service metadata
    >>> metadata = client.get_metadata(
    ...     service_name="ZSD_CUSTOMER_API",
    ...     odata_version="v4"
    ... )
"""

__version__ = "1.0.0"
__author__ = "Vaibhav Goel"
__license__ = "Apache-2.0"

from .client import SAPODataClient
from .exceptions import (
    SAPODataError,
    SAPConnectionError,
    SAPAuthenticationError,
    SAPServiceError,
    SAPCSRFTokenError,
    SAPMetadataError,
)
from .response import ODataResponse
from .metadata import MetadataParser, EntityType, Property

__all__ = [
    # Main client
    "SAPODataClient",
    # Response
    "ODataResponse",
    # Metadata
    "MetadataParser",
    "EntityType", 
    "Property",
    # Exceptions
    "SAPODataError",
    "SAPConnectionError",
    "SAPAuthenticationError",
    "SAPServiceError",
    "SAPCSRFTokenError",
    "SAPMetadataError",
    # Version
    "__version__",
]
