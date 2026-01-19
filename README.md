# SAP OData Python

Simple, AI/LLM-friendly Python client for SAP OData V2 and V4 services.

[![PyPI](https://img.shields.io/pypi/v/sap-odata-python)](https://pypi.org/project/sap-odata-python/)
[![Python](https://img.shields.io/pypi/pyversions/sap-odata-python)](https://pypi.org/project/sap-odata-python/)
[![License](https://img.shields.io/pypi/l/sap-odata-python)](https://github.com/vaibhavgoel-github-1986/sap-odata-python/blob/main/LICENSE)

## Why This Library?

- **SAP-First Design**: Built specifically for SAP OData services (V2 Gateway & V4 RAP)
- **AI/LLM Friendly**: Single generic function design - perfect for AI agents and automation
- **Simple API**: One client, one method signature for all operations
- **Automatic URL Building**: Handles complex SAP URL patterns automatically
- **Input Validation**: Clear error messages for missing parameters
- **Raw Responses**: Returns actual API response - use helper methods to extract data
- **Helper Methods**: `get_value()` and `get_next_link()` for easy data extraction

## Installation

```bash
pip install sap-odata-python
```

## Quick Start - SAP Systems

```python
from sap_odata import ODataClient

# Connect to SAP system (sap_mode=True is the default)
client = ODataClient(
    "https://sap-system.company.com:44300",
    username="your_user",
    password="your_password",
    client="100"
)

# SAP OData V4 (RAP Services)
data = client.get(
    service="zsd_my_service",
    entity="MyEntity",
    version="v4",
    namespace="zsb_my_service",  # Required for V4
    filter="Status eq 'ACTIVE'",
    top=10
)

# SAP OData V2 (Gateway Services)
data = client.get(
    service="ZMY_SALESORDER_SRV",
    entity="SalesOrderSet",
    version="v2",
    filter="Status eq 'OPEN'",
    top=10
)

# Use helper methods to extract data
for item in client.get_value(data, "v2"):
    print(item)
```

## SAP URL Patterns (Handled Automatically)

The library automatically builds correct SAP URLs:

| Version | URL Pattern |
|---------|-------------|
| **V4** | `/sap/opu/odata4/sap/{namespace}/srvd_a2x/sap/{service}/0001/{entity}` |
| **V2** | `/sap/opu/odata/sap/{service}/{entity}` |

You just provide `service`, `entity`, and `namespace` (for V4) - the library builds the full URL.

## API Reference

### ODataClient Constructor

```python
client = ODataClient(
    host,                    # SAP system URL (e.g., "https://sap.company.com:44300")
    username="",             # SAP username
    password="",             # SAP password
    client="",               # SAP client number (e.g., "100", "120")
    sap_mode=True,           # True for SAP systems (default), False for other OData services
    verify_ssl=True,         # SSL certificate verification
    timeout=60               # Request timeout in seconds
)
```

### Methods

| Method | Description |
|--------|-------------|
| `get(service, entity, version, namespace, **params)` | Read data (GET) |
| `post(service, entity, data, version, namespace)` | Create record (POST) |
| `patch(service, entity, data, version, namespace)` | Update record (PATCH) |
| `delete(service, entity, version, namespace)` | Delete record (DELETE) |
| `metadata(service, version, namespace)` | Get service metadata (XML) |
| `get_value(response, version)` | Extract entity array from response |
| `get_next_link(response, version)` | Extract pagination URL from response |

### Query Parameters (for GET)

| Parameter | Example | Description |
|-----------|---------|-------------|
| `top` | `top=10` | Limit number of results |
| `skip` | `skip=20` | Skip records (pagination) |
| `filter` | `filter="Price gt 100"` | OData filter expression |
| `select` | `select="ID,Name,Price"` | Select specific fields |
| `expand` | `expand="Customer,Items"` | Expand navigation properties |
| `orderby` | `orderby="Name asc"` | Sort results |

## SAP OData V4 (RAP Services)

```python
client = ODataClient(
    "https://sap-system.company.com:44300",
    username="user",
    password="pass",
    client="100"
)

# Simple query
data = client.get(
    service="zmy_product_api",
    entity="Products",
    version="v4",
    namespace="zsb_product_api",
    filter="ProductID eq '12345'"
)

# Complex nested $expand
data = client.get(
    service="zmy_order_api",
    entity="Orders",
    version="v4",
    namespace="zsb_order_api",
    filter="OrderID eq '12345'",
    expand="Customer($expand=Contacts),LineItems($expand=Product,Discounts($expand=Details)),Payments($expand=BankAccount)"
)

# Access nested data using helper method
for order in client.get_value(data, "v4"):
    print(f"Order: {order['OrderID']}")
    for line in order.get("LineItems", []):
        print(f"  Line Item: {line['ProductName']}")
```

## SAP OData V2 (Gateway Services)

```python
# Simple query
data = client.get(
    service="ZMY_SALESORDER_SRV",
    entity="SalesOrderSet",
    version="v2",
    top=10,
    filter="Status eq 'OPEN'"
)

# Entity with key in path
data = client.get(
    service="ZMY_CUSTOMER_SRV",
    entity="CustomerSet(CustomerID='CUST001',Region='US')",
    version="v2"
)

# Complex nested $expand (V2 style with /)
data = client.get(
    service="ZMY_ORDER_SRV",
    entity="OrderSet(OrderID='12345')",
    version="v2",
    expand="OrderToCustomer/CustomerToContacts,OrderToItems/ItemToProduct,OrderToItems/ItemToDiscounts,OrderToPayments/PaymentToBankAccount"
)

# V2 nested results are in "results" arrays
for order in client.get_value(data, "v2"):
    print(f"Order: {order['OrderID']}")
    for item in order.get("OrderToItems", {}).get("results", []):
        print(f"  Item: {item['ProductName']}")
```

## Write Operations

```python
# POST - Create
new_order = client.post(
    service="ZMY_SALESORDER_SRV",
    entity="SalesOrderSet",
    data={"CustomerID": "CUST001", "Amount": 1000},
    version="v2"
)

# PATCH - Update
client.patch(
    service="ZMY_SALESORDER_SRV",
    entity="SalesOrderSet('12345')",
    data={"Status": "APPROVED"},
    version="v2"
)

# DELETE
client.delete(
    service="ZMY_SALESORDER_SRV",
    entity="SalesOrderSet('12345')",
    version="v2"
)
```

## Get Service Metadata

```python
# V4 metadata
xml = client.metadata(service="zmy_product_api", namespace="zsb_product_api")

# V2 metadata
xml = client.metadata(service="ZMY_SALESORDER_SRV", version="v2")

print(xml)  # Returns XML string with entity definitions
```

## Using with Non-SAP OData Services

For public OData services like Northwind or TripPin, set `sap_mode=False`:

```python
from sap_odata import ODataClient

# Non-SAP OData service - set sap_mode=False
client = ODataClient("https://services.odata.org", sap_mode=False)

# Northwind V4
data = client.get("V4/Northwind/Northwind.svc", "Products", top=5)

# Northwind V2
data = client.get("V2/Northwind/Northwind.svc", "Products", version="v2", top=5)

# TripPin
data = client.get("TripPinRESTierService", "People", top=3)
data = client.get("TripPinRESTierService", "Airlines")
```

**Note**: `sap_mode=True` is the default since this library is designed for SAP systems.

## Response Format

Responses are returned **raw** (as received from the API):

```python
# V4 response format
{"@odata.context": "...", "value": [{...}, {...}], "@odata.nextLink": "..."}

# V2 response format  
{"d": [{...}, {...}]}  # or {"d": {"results": [...], "__next": "..."}}
```

### Helper Methods

Use helper methods to extract data consistently:

```python
# Extract entities from response
items = client.get_value(response, "v4")  # Returns list
items = client.get_value(response, "v2")  # Returns list

# Get pagination URL
next_url = client.get_next_link(response, "v4")  # Returns URL or ""
next_url = client.get_next_link(response, "v2")  # Returns URL or ""
```

### Pagination Example

```python
# Fetch all pages
all_items = []
response = client.get("ZMY_SRV", "ItemSet", version="v2", top=100)

while True:
    all_items.extend(client.get_value(response, "v2"))
    next_link = client.get_next_link(response, "v2")
    if not next_link:
        break
    # Fetch next page using the full URL
    response = client.session.get(next_link).json()

print(f"Total items: {len(all_items)}")
```

## Error Handling

```python
from sap_odata import ODataClient, ODataError, ODataConnectionError, ODataAuthError

try:
    client = ODataClient("https://sap.company.com", "user", "pass", client="100")
    data = client.get("zsd_my_service", "MyEntity", version="v4", namespace="zsb_my_service")
except ODataAuthError:
    print("Authentication failed - check username/password")
except ODataConnectionError as e:
    print(f"Connection failed: {e}")
except ODataError as e:
    print(f"OData error: {e}")
```

### Validation Errors

The library validates inputs and provides clear error messages:

```python
# Missing namespace for V4
client.get("zsd_my_service", "MyEntity", version="v4")
# ODataError: Namespace is required for SAP OData V4 services.

# Invalid version
client.get("service", "entity", version="v3")
# ODataError: Invalid version 'v3'. Must be 'v2' or 'v4'
```

## Context Manager

```python
with ODataClient("https://sap-system.com", "user", "pass", client="100") as client:
    data = client.get("ZMY_SALESORDER_SRV", "SalesOrderSet", version="v2")
# Session automatically closed
```

## For AI/LLM Integration

This library is designed to be AI-friendly with a simple, consistent API:

```python
# Single function signature for all SAP OData calls
client.get(
    service="<service_name>",
    entity="<entity_name>",
    version="v2" | "v4",
    namespace="<namespace>",  # Required for V4
    filter="<odata_filter>",
    select="<fields>",
    expand="<navigations>",
    top=<number>
)
```

## License

Apache 2.0

## Links

- [PyPI Package](https://pypi.org/project/sap-odata-python/)
- [GitHub Repository](https://github.com/vaibhavgoel-github-1986/sap-odata-python)
- [OData Protocol](https://www.odata.org/)
