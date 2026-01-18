# SAP OData Python

Simple Python client for OData V2 and V4 services.

[![Tests](https://github.com/vaibhavgoel-github-1986/sap-odata-python/actions/workflows/tests.yml/badge.svg)](https://github.com/vaibhavgoel-github-1986/sap-odata-python/actions)
[![PyPI](https://img.shields.io/pypi/v/sap-odata-python)](https://pypi.org/project/sap-odata-python/)
[![Python](https://img.shields.io/pypi/pyversions/sap-odata-python)](https://pypi.org/project/sap-odata-python/)

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

## SAP OData V4 (RAP Services)

```python
client = ODataClient(
    host="https://sap-system.company.com",
    username="user",
    password="pass",
    client="100"
)

# Simple query
data = client.get(
    service="zsd_get_subs_v2",
    entity="Header",
    version="v4",
    namespace="zsb_get_subs_v2",
    filter="subscriptionRefId eq 'SR12345'"
)

# Complex nested $expand
data = client.get(
    service="zsd_get_subs_v2",
    entity="Header",
    version="v4",
    namespace="zsb_get_subs_v2",
    filter="subscriptionRefId eq 'SR12345'",
    expand="partyAccounts($expand=contacts),majorLines($expand=smartAccounts,partyAccounts($expand=contacts)),minorLines($expand=discountAttributes)"
)

# Access nested data
for header in data["value"]:
    print(f"Subscription: {header['subscriptionId']}")
    for line in header.get("majorLines", []):
        print(f"  Major Line: {line['partName']}")
```

## SAP OData V2 (Gateway Services)

```python
# Simple query
data = client.get(
    service="ZS4_SALES_ORDER_SRV",
    entity="SalesOrderSet",
    version="v2",
    top=10,
    filter="Status eq 'OPEN'"
)

# Entity with key in path
data = client.get(
    service="ZS4_CCW_SEND_SUBSCR_SNAPSHOT_SRV_01",
    entity="HeaderSet(SubscriptionRefId='SR12345',WebOrderId='',SubscriptionId='')",
    version="v2"
)

# Complex nested $expand (V2 style with /)
data = client.get(
    service="ZS4_CCW_SEND_SUBSCR_SNAPSHOT_SRV_01",
    entity="HeaderSet(SubscriptionRefId='SR12345',WebOrderId='',SubscriptionId='')",
    version="v2",
    expand="HeaderToPrtyAccts/PrtyAcctsToContacts,HeaderToMjrLine/MjrLineToSmartAcct,HeaderToMjrLine/MjrLineToDscntAttr,HeaderToMnrLines/MnrLinesToDscntAttr"
)

# V2 nested results are in "results" arrays
for header in data["value"]:
    print(f"Subscription: {header['SubscriptionId']}")
    for line in header.get("HeaderToMjrLine", {}).get("results", []):
        print(f"  Major Line: {line['PartName']}")
```

## Write Operations

```python
# POST - Create
new_order = client.post(
    service="ZSALESORDER_SRV",
    entity="SalesOrderSet",
    data={"CustomerID": "CUST001", "Amount": 1000},
    version="v2"
)

# PATCH - Update
client.patch(
    service="ZSALESORDER_SRV",
    entity="SalesOrderSet('12345')",
    data={"Status": "APPROVED"},
    version="v2"
)

# DELETE
client.delete(
    service="ZSALESORDER_SRV",
    entity="SalesOrderSet('12345')",
    version="v2"
)
```

## Get Service Metadata

```python
# V4 metadata
xml = client.metadata(service="zsd_get_subs_v2", namespace="zsb_get_subs_v2")

# V2 metadata
xml = client.metadata(service="ZSALESORDER_SRV", version="v2")

print(xml)  # Returns XML string with entity definitions
```

## API Reference

### ODataClient

```python
client = ODataClient(
    host="https://sap-system.com",  # Base URL
    username="user",                 # Optional: for auth
    password="pass",                 # Optional: for auth
    client="100",                    # Optional: SAP client
    verify_ssl=True,                 # Optional: SSL verification
    timeout=60                       # Optional: request timeout
)
```

### Methods

| Method | Description |
|--------|-------------|
| `get(service, entity, version="v4", namespace="", **params)` | Read data |
| `post(service, entity, data, version="v4", namespace="")` | Create record |
| `patch(service, entity, data, version="v4", namespace="")` | Update record |
| `delete(service, entity, version="v4", namespace="")` | Delete record |
| `metadata(service, version="v4", namespace="")` | Get XML metadata |

### Query Parameters

| Param | Example | Description |
|-------|---------|-------------|
| `top` | `top=10` | Limit results |
| `skip` | `skip=20` | Skip records (pagination) |
| `filter` | `filter="Price gt 100"` | Filter expression |
| `select` | `select="ID,Name"` | Select fields |
| `expand` | `expand="Orders"` | Expand navigation properties |
| `orderby` | `orderby="Name asc"` | Sort results |

### Response Format

All responses are normalized to:
```python
{"value": [{"field": "value"}, ...]}
```

- **V4**: Native format, returned as-is
- **V2**: Converted from `{"d": {"results": [...]}}` to `{"value": [...]}`

## Context Manager

```python
with ODataClient("https://sap-system.com", "user", "pass", client="100") as client:
    data = client.get("ZSALESORDER_SRV", "SalesOrderSet", version="v2")
# Session automatically closed
```

## License

Apache 2.0
