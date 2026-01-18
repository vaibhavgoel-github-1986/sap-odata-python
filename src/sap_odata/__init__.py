"""
SAP OData Python Client - Enterprise-ready OData client for SAP systems.

This library provides a Pythonic interface for interacting with SAP OData services,
supporting both OData V2 (Gateway) and V4 (RAP/CAP) protocols.

Example:
    >>> from sap_odata import ODataClient
    >>> client = ODataClient(
    ...     host="https://sap-system.com",
    ...     username="user",
    ...     password="pass",
    ...     client="100"
    ... )
    >>> service = client.service("ZSD_API", version="v4")
    >>> customers = service.entity("Customers").get()

"""

__version__ = "1.0.0"
__author__ = "Vaibhav Goel"
__license__ = "Apache-2.0"

from .client import ODataClient
from .config import ODataConfig
from .service import ODataService
from .query import QueryBuilder
from .metadata import Metadata, EntityType, EntitySet, Property
from .exceptions import (
    ODataError,
    ODataConnectionError,
    ODataAuthenticationError,
    ODataNotFoundError,
    ODataValidationError,
    ODataCSRFError,
)
from .response import ODataResponse, EntityCollection, Entity

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__license__",
    # Main classes
    "ODataClient",
    "ODataConfig",
    "ODataService",
    "QueryBuilder",
    # Metadata
    "Metadata",
    "EntityType",
    "EntitySet",
    "Property",
    # Response
    "ODataResponse",
    "EntityCollection",
    "Entity",
    # Exceptions
    "ODataError",
    "ODataConnectionError",
    "ODataAuthenticationError",
    "ODataNotFoundError",
    "ODataValidationError",
    "ODataCSRFError",
]
