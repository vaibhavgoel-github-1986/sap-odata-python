# SAP OData Python

Simple Python client for OData V2 and V4 services.

## Installation

```bash
pip install sap-odata-python
```

## Quick Start

```python
from sap_odata import ODataClient

# Public OData service
client = ODataClient("https://services.odata.org")

# GET data
data = client.get("V4/Northwind/Northwind.svc", "Products", top=5)
for product in data["value"]:
    print(product["ProductName"])

# With filters
data = client.get(
    "V4/Northwind/Northwind.svc",
    "Products",
    filter="UnitPrice gt 20",
    select="ProductID,ProductName,UnitPrice",
    top=10
)
```

## SAP System

```python
client = ODataClient(
    host="https://sap-system.company.com",
    username="user",
    password="pass",
    client="100"
)

# V4 RAP service
data = client.get(
    "ZSD_CUSTOMER_API",
    "Customers",
    namespace="ZSB_CUSTOMER_API",
    filter="Country eq 'US'"
)

# V2 Gateway service
data = client.get("ZSALESORDER_SRV", "SalesOrderSet", version="v2", top=10)
```

## API

### Methods

```python
client.get(service, entity, version="v4", **query_params)   # Read
client.post(service, entity, data, version="v4")            # Create
client.patch(service, entity, data, version="v4")           # Update
client.delete(service, entity, version="v4")                # Delete
client.metadata(service, version="v4")                      # Get XML metadata
```

### Query Parameters

| Param | Example |
|-------|---------|
| `top` | `top=10` |
| `skip` | `skip=20` |
| `filter` | `filter="Price gt 100"` |
| `select` | `select="ID,Name"` |
| `expand` | `expand="Orders"` |
| `orderby` | `orderby="Name asc"` |

## License

Apache 2.0
