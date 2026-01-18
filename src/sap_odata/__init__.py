"""
SAP OData Python - A simple OData V2/V4 client library.

Example:
    >>> from sap_odata import ODataClient
    >>> client = ODataClient("https://services.odata.org")
    >>> response = client.get("V4/Northwind/Northwind.svc", "Products", top=5)
    >>> for product in response["value"]:
    ...     print(product["ProductName"])
"""

__version__ = "1.0.0"
__author__ = "Vaibhav Goel"

from .client import ODataClient
from .exceptions import ODataError, ODataConnectionError, ODataAuthError

__all__ = ["ODataClient", "ODataError", "ODataConnectionError", "ODataAuthError"]
