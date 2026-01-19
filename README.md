# SAP OData Python

Simple, AI/LLM-friendly Python client for SAP OData V2 and V4 services.

[![PyPI](https://img.shields.io/pypi/v/sap-odata-python)](https://pypi.org/project/sap-odata-python/)
[![Python](https://img.shields.io/pypi/pyversions/sap-odata-python)](https://pypi.org/project/sap-odata-python/)
[![License](https://img.shields.io/pypi/l/sap-odata-python)](https://github.com/vaibhavgoel-github-1986/sap-odata-python/blob/main/LICENSE)

## Features

- **SAP-First Design** - Built specifically for SAP OData services (V2 Gateway & V4 RAP)
- **AI/LLM Friendly** - Single generic function design, perfect for AI agents
- **Simple API** - One client, one method signature for all operations
- **Automatic URL Building** - Handles complex SAP URL patterns automatically
- **Input Validation** - Clear error messages for missing parameters
- **Raw Responses** - Returns actual API response with helper methods to extract data

## Installation

```
pip install sap-odata-python
```

## Quick Start

```python
from sap_odata import ODataClient

# Connect to SAP system (sap_mode=True is default)
client = ODataClient(
    "https://sap-system.company.com:44300",
    username="your_user",
    password="your_password",
    client="100"
)

# SAP OData V4 (RAP Services)
response = client.get(
    service="zsd_my_service",
    entity="MyEntity",
    version="v4",
    namespace="zsb_my_service",
    top=10
)

# SAP OData V2 (Gateway Services)
response = client.get(
    service="ZMY_SALESORDER_SRV",
    entity="SalesOrderSet",
    version="v2",
    top=10
)

# Access data directly
for item in response["d"]:  # V2 format
    print(item)
```

## SAP OData V4 Examples

```python
# Simple query with filter
response = client.get(
    service="zsd_product_api",
    entity="Products",
    version="v4",
    namespace="zsb_product_api",
    filter="ProductID eq '12345'",
    select="ProductID,Name,Price"
)

# Complex nested $expand
response = client.get(
    service="zsd_order_api",
    entity="Orders",
    version="v4",
    namespace="zsb_order_api",
    filter="OrderID eq '12345'",
    expand="Customer,LineItems($expand=Product)"
)

# Access nested data
for order in response["value"]:  # V4 format
    print(f"Order: {order['OrderID']}")
    for item in order.get("LineItems", []):
        print(f"  Item: {item['ProductName']}")

# Count only (no data returned) - calls /Entity/$count
total_products = client.count(
    service="zsd_product_api",
    entity="Products",
    version="v4",
    namespace="zsb_product_api"
)
print(f"Total products: {total_products}")  # 245

# Count with filter
open_orders = client.count(
    service="zsd_order_api",
    entity="Orders",
    version="v4",
    namespace="zsb_order_api",
    filter="Status eq 'OPEN'"
)
print(f"Open orders: {open_orders}")  # 42

# Inline count (data + total count)
response = client.get(
    service="zsd_product_api",
    entity="Products",
    version="v4",
    namespace="zsb_product_api",
    top=10,
    count=True  # Adds $count=true
)
total = client.get_count(response, "v4")  # from @odata.count
items = client.get_value(response, "v4")  # from value[]
print(f"Showing {len(items)} of {total} products")
```

## SAP OData V2 Examples

```python
# Query with filter and select
response = client.get(
    service="ZMY_SALESORDER_SRV",
    entity="SalesOrderSet",
    version="v2",
    filter="Status eq 'OPEN'",
    select="OrderID,CustomerID,Amount",
    top=100
)

# Count only (V2)
total = client.count(
    service="ZMY_SALESORDER_SRV",
    entity="SalesOrderSet",
    version="v2"
)
print(f"Total orders: {total}")

# Inline count (V2)
response = client.get(
    service="ZMY_SALESORDER_SRV",
    entity="SalesOrderSet",
    version="v2",
    top=20,
    count=True
)
# V2 response: {"d": {"__count": "245", "results": [...]}}
total = client.get_count(response, "v2")  # from d.__count
items = client.get_value(response, "v2")  # from d.results or d[]

# Entity with key in path
response = client.get(
    service="ZMY_CUSTOMER_SRV",
    entity="CustomerSet('CUST001')",
    version="v2"
)

# Complex nested $expand (V2 uses / for nested)
response = client.get(
    service="ZMY_ORDER_SRV",
    entity="OrderSet",
    version="v2",
    expand="OrderToCustomer,OrderToItems/ItemToProduct"
)

# V2 nested results use "results" arrays
for order in response["d"]:  # or response["d"]["results"] depending on service
    for item in order.get("OrderToItems", {}).get("results", []):
        print(f"  Item: {item['ProductName']}")
```

## SAP URL Patterns (Handled Automatically)

| Version | URL Pattern |
|---------|-------------|
| V4 | `/sap/opu/odata4/sap/{namespace}/srvd_a2x/sap/{service}/0001/{entity}` |
| V2 | `/sap/opu/odata/sap/{service}/{entity}` |

You just provide `service`, `entity`, and `namespace` (for V4) - the library builds the full URL.

## API Reference

### Constructor

```python
client = ODataClient(
    host,              # SAP system URL
    username="",       # SAP username
    password="",       # SAP password
    client="",         # SAP client number (e.g., "100")
    sap_mode=True,     # True for SAP, False for other OData services
    verify_ssl=True,   # SSL verification
    timeout=60         # Request timeout
)
```

### Methods

| Method | Description |
|--------|-------------|
| `get(service, entity, version, namespace, **params)` | Read data (GET) |
| `post(service, entity, data, version, namespace)` | Create record (POST) |
| `put(service, entity, data, version, namespace)` | Replace record (PUT) |
| `patch(service, entity, data, version, namespace)` | Update record (PATCH) |
| `delete(service, entity, version, namespace)` | Delete record (DELETE) |
| `count(service, entity, version, namespace, **params)` | Get count only (no data) |
| `metadata(service, version, namespace)` | Get service metadata (XML) |
| `get_value(response, version)` | Extract data list from response |
| `get_count(response, version)` | Extract inline count from response |
| `get_next_link(response, version)` | Extract pagination URL |

### Query Parameters

| Parameter | Example | Description |
|-----------|---------|-------------|
| `top` | `top=10` | Limit results |
| `skip` | `skip=20` | Skip records |
| `filter` | `filter="Price gt 100"` | Filter expression |
| `select` | `select="ID,Name"` | Select fields |
| `expand` | `expand="Items"` | Expand navigation |
| `orderby` | `orderby="Name asc"` | Sort results |
| `count` | `count=True` | Include inline count |
| `search` | `search="keyword"` | Free text search |

## Counting Records

Two ways to get counts:

### 1. Count Only (no data) - `/Entity/$count`

```python
# Count all products
total = client.count("zsd_product_api", "Products", version="v4", namespace="zsb_product_api")
print(total)  # 245

# Count with filter
open_orders = client.count("ZMY_SRV", "Orders", version="v2", filter="Status eq 'OPEN'")
print(open_orders)  # 42
```

### 2. Inline Count (with data) - `$count=true`

```python
# Get data with total count
response = client.get("zsd_product_api", "Products", version="v4", namespace="zsb_product_api", 
                      top=10, count=True)

# V4: {"@odata.count": 245, "value": [...]}
total = client.get_count(response, "v4")  # 245
items = client.get_value(response, "v4")  # [...]

# V2: {"d": {"__count": "245", "results": [...]}}
total = client.get_count(response, "v2")  # 245
```

## Response Format

Responses are returned raw (as received from the API):

```python
# V4 response
{"@odata.context": "...", "value": [...], "@odata.nextLink": "...", "@odata.count": 100}

# V2 response
{"d": [...]}  # or {"d": {"results": [...], "__next": "...", "__count": "100"}}
```

### Helper Methods

Use helper methods to extract data from responses:

```python
response = client.get("service", "Products", top=10, count=True)

# Extract data list
items = client.get_value(response, "v4")  # Returns list from "value" or "d"

# Get total count (if $count was requested)
total = client.get_count(response, "v4")  # Returns @odata.count or -1

# Get next page URL
next_url = client.get_next_link(response, "v4")  # from @odata.nextLink
next_url = client.get_next_link(response, "v2")  # from d.__next
```

## Non-SAP OData Services

For public services like Northwind, set `sap_mode=False`:

```python
client = ODataClient("https://services.odata.org", sap_mode=False)

# Northwind V4
data = client.get("V4/Northwind/Northwind.svc", "Products", top=5)

# Northwind V2
data = client.get("V2/Northwind/Northwind.svc", "Products", version="v2", top=5)
```

## Error Handling

```python
from sap_odata import ODataClient, ODataError, ODataConnectionError, ODataAuthError

try:
    data = client.get("zsd_my_service", "MyEntity", version="v4", namespace="zsb_my_service")
except ODataAuthError:
    print("Authentication failed")
except ODataConnectionError as e:
    print(f"Connection failed: {e}")
except ODataError as e:
    print(f"OData error: {e}")
```

## Context Manager

```python
with ODataClient("https://sap.company.com", "user", "pass", client="100") as client:
    data = client.get("ZMY_SRV", "OrderSet", version="v2")
# Session automatically closed
```

## License

Apache 2.0

## Links

- [GitHub Repository](https://github.com/vaibhavgoel-github-1986/sap-odata-python)
- [OData Protocol](https://www.odata.org/)
