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

# Extract data using helper methods
items = client.get_value(response, "v4")
for item in items:
    print(item)
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
| `patch(service, entity, data, version, namespace)` | Update record (PATCH) |
| `delete(service, entity, version, namespace)` | Delete record (DELETE) |
| `metadata(service, version, namespace)` | Get service metadata (XML) |
| `get_value(response, version)` | Extract entity array from response |
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

## Response Format

Responses are returned raw (as received from the API):

```python
# V4 response
{"@odata.context": "...", "value": [...], "@odata.nextLink": "..."}

# V2 response
{"d": [...]}  # or {"d": {"results": [...], "__next": "..."}}
```

### Helper Methods

```python
# Extract entities from response
items = client.get_value(response, "v4")
items = client.get_value(response, "v2")

# Get pagination URL
next_url = client.get_next_link(response, "v4")
next_url = client.get_next_link(response, "v2")
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
