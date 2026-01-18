# SAP OData Python Client

[![PyPI version](https://badge.fury.io/py/sap-odata-python.svg)](https://badge.fury.io/py/sap-odata-python)
[![Python Versions](https://img.shields.io/pypi/pyversions/sap-odata-python.svg)](https://pypi.org/project/sap-odata-python/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

**A unified Python OData client supporting both OData V2 and V4 protocols.**

This library provides a simple, **AI/LLM-friendly** interface for interacting with OData services. Unlike other libraries that use complex builder patterns, this client uses a **single generic function approach** optimized for AI tool calling and MCP (Model Context Protocol) integration.

## ✨ Features

- 🔄 **Dual Protocol Support**: First-class support for both OData V2 and V4
- 🤖 **AI/LLM Optimized**: Single generic function design, perfect for AI tool calling
- 🏢 **SAP-Optimized**: Built for SAP systems (S/4HANA, BTP, Gateway) but works with any OData service
- 🔐 **Auto CSRF Handling**: Automatic CSRF token management for write operations
- 📊 **Metadata Parsing**: Full metadata parsing with entity type inspection
- 🔄 **Response Normalization**: Consistent response format across V2/V4
- 📝 **Type Hints**: Full type hints for IDE support

## 📦 Installation

```bash
pip install sap-odata-python
```

## 🚀 Quick Start

### Basic Usage - Single Generic Function

```python
from sap_odata import SAPODataClient

# Connect to any OData service
client = SAPODataClient(
    host="https://services.odata.org",
    username="",  # Public service, no auth needed
    password="",
    client=""
)

# GET: Retrieve products (V4)
response = client.call_odata(
    http_method="GET",
    service_name="V4/Northwind/Northwind.svc",
    entity_name="Products",
    odata_version="v4",
    query_parameters={
        "$filter": "UnitPrice gt 20",
        "$select": "ProductID,ProductName,UnitPrice",
        "$top": 10,
        "$orderby": "ProductName"
    }
)

# Access data
for product in response.value:
    print(f"{product['ProductID']}: {product['ProductName']} - ${product['UnitPrice']}")
```

### SAP System Example

```python
from sap_odata import SAPODataClient

# Connect to SAP system
client = SAPODataClient(
    host="https://your-sap-system.com",
    username="your_user",
    password="your_password",
    client="100"  # SAP client number
)

# GET: Retrieve customers with filter (V4 RAP service)
response = client.call_odata(
    http_method="GET",
    service_name="ZSD_CUSTOMER_API",
    service_namespace="ZSB_CUSTOMER_API",  # Required for SAP V4
    entity_name="Customers",
    odata_version="v4",
    query_parameters={
        "$filter": "Country eq 'US' and Active eq true",
        "$select": "CustomerID,Name,Country",
        "$top": 10
    }
)
```

### All HTTP Methods

```python
# POST: Create new record
response = client.call_odata(
    http_method="POST",
    service_name="ZSD_CUSTOMER_API",
    entity_name="Customers",
    odata_version="v4",
    request_body={
        "CustomerID": "CUST001",
        "Name": "ACME Corporation",
        "Country": "US",
        "Active": True
    }
)

# PATCH: Update specific fields
response = client.call_odata(
    http_method="PATCH",
    service_name="ZSD_CUSTOMER_API",
    entity_name="Customers('CUST001')",
    odata_version="v4",
    request_body={"Status": "Inactive"}
)

# DELETE: Remove entity
response = client.call_odata(
    http_method="DELETE",
    service_name="ZSD_CUSTOMER_API",
    entity_name="Customers('CUST001')",
    odata_version="v4"
)
```

### OData V2 Example

```python
# V2 service (Northwind public service)
response = client.call_odata(
    http_method="GET",
    service_name="V2/Northwind/Northwind.svc",
    entity_name="Categories",
    odata_version="v2",
    query_parameters={
        "$expand": "Products",
        "$top": 5
    }
)

for category in response.value:
    print(f"{category['CategoryName']}: {len(category.get('Products', []))} products")
```

### Get Service Metadata

```python
# Get raw metadata XML
xml = client.get_metadata(
    service_name="V4/Northwind/Northwind.svc",
    odata_version="v4"
)

# Get parsed metadata
metadata = client.get_metadata(
    service_name="V4/Northwind/Northwind.svc",
    odata_version="v4",
    parse=True
)

# Explore entity types
for entity in metadata.entity_types:
    print(f"\n{entity.name}:")
    for prop in entity.properties:
        key_marker = " [KEY]" if prop.is_key else ""
        print(f"  - {prop.name}: {prop.type}{key_marker}")
```

## 🎯 Design Philosophy

This library uses a **single generic function approach** instead of fluent/builder patterns:

| Aspect | Builder Pattern (others) | Generic Function (this lib) |
|--------|-------------------------|----------------------------|
| **AI/LLM Friendliness** | ❌ Hard - method chaining | ✅ Easy - single function |
| **MCP/Tool Calling** | ❌ Complex to serialize | ✅ Just JSON parameters |
| **Learning Curve** | ⚠️ Learn many methods | ✅ One function, explicit params |
| **Debugging** | ⚠️ Hidden in chain | ✅ All params visible |

### Why This Design?

1. **LLMs excel at generating function calls** with named parameters
2. **MCP/Tool calling APIs** work perfectly with explicit parameters  
3. **All parameters visible** in one place for easy debugging
4. **Easy serialization** - just JSON, no complex object state

## 📖 API Reference

### `SAPODataClient`

```python
client = SAPODataClient(
    host: str,           # OData service base URL
    username: str,       # Username (empty for public services)
    password: str,       # Password (empty for public services)
    client: str = "100", # SAP client number (for SAP systems)
    verify_ssl: bool = True,
    timeout: int = 120
)
```

### `call_odata()`

```python
response = client.call_odata(
    http_method: str,        # GET, POST, PUT, PATCH, DELETE
    service_name: str,       # OData service name/path
    entity_name: str,        # Entity name or path with keys
    service_namespace: str,  # Required for SAP V4, optional otherwise
    odata_version: str,      # "v2" or "v4"
    query_parameters: dict,  # $filter, $select, $top, etc.
    request_body: dict,      # For POST/PUT/PATCH
    headers: dict            # Additional headers (optional)
)
```

### Query Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `$filter` | Filter records | `"UnitPrice gt 100 and Discontinued eq false"` |
| `$select` | Select fields | `"ProductID,ProductName,UnitPrice"` |
| `$expand` | Include related | `"Category,Supplier"` |
| `$top` | Limit results | `10` |
| `$skip` | Pagination offset | `20` |
| `$orderby` | Sort results | `"ProductName asc, UnitPrice desc"` |
| `$count` | Include count | `true` |

### `ODataResponse`

```python
response.status_code  # HTTP status code
response.data         # Normalized data dict  
response.value        # List of entities
response.first        # First entity or None
response.is_success   # True if 2xx
response.is_empty     # True if no data
response.has_more     # True if pagination available
response.count        # Total count (if requested)
response.next_link    # Pagination URL
```

## 🧪 Testing with Public Services

The library is tested against the public Northwind OData services:

- **V4**: `https://services.odata.org/V4/Northwind/Northwind.svc/`
- **V2**: `https://services.odata.org/V2/Northwind/Northwind.svc/`

```bash
# Run tests
pip install -e ".[dev]"
pytest -v
```

## 📄 License

Apache License 2.0 - see [LICENSE](LICENSE) for details.

## 🤝 Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.
