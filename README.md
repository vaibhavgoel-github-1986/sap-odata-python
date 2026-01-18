# SAP OData Python Client

[![Build Status](https://github.com/vaibhavgoel-github-1986/sap-odata-python/actions/workflows/tests.yml/badge.svg)](https://github.com/vaibhavgoel-github-1986/sap-odata-python/actions)
[![PyPI version](https://badge.fury.io/py/sap-odata-python.svg)](https://badge.fury.io/py/sap-odata-python)
[![Python Versions](https://img.shields.io/pypi/pyversions/sap-odata-python.svg)](https://pypi.org/project/sap-odata-python/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![codecov](https://codecov.io/gh/vaibhavgoel-github-1986/sap-odata-python/branch/main/graph/badge.svg)](https://codecov.io/gh/vaibhavgoel-github-1986/sap-odata-python)

**Enterprise-ready Python OData client for SAP systems supporting both OData V2 and V4 protocols.**

This library provides a Pythonic, intuitive interface for interacting with SAP OData services. Unlike other libraries that only support V2, this client seamlessly handles both OData V2 (Gateway) and V4 (RAP/CAP) services with a unified API.

## ✨ Features

- 🔄 **Dual Protocol Support**: First-class support for both OData V2 and V4
- 🏢 **SAP-Optimized**: Built specifically for SAP systems (S/4HANA, BTP, Gateway)
- 🔐 **Auto CSRF Handling**: Automatic CSRF token management for write operations
- 📊 **Metadata Parsing**: Full metadata parsing with entity type inspection
- 🔍 **Query Builder**: Fluent query builder for $filter, $select, $expand, etc.
- 📦 **Batch Operations**: Support for batch requests (changeset)
- 🔄 **Response Normalization**: Consistent response format across V2/V4
- ⚡ **Async Support**: Optional async/await support for high-performance apps
- 🧪 **Well Tested**: Comprehensive test suite with >90% coverage

## 📦 Installation

```bash
pip install sap-odata-python
```

## 🚀 Quick Start

### Basic Usage

```python
from sap_odata import ODataClient

# Connect to SAP OData V4 service (RAP/CAP)
client = ODataClient(
    host="https://your-sap-system.com",
    username="your_user",
    password="your_password",
    client="100",  # SAP client
)

# Access a V4 service
service = client.service(
    name="ZSD_CUSTOMER_API",
    namespace="ZSB_CUSTOMER_API",  # Required for V4
    version="v4"
)

# Read entities
customers = service.entity("Customers").get()
for customer in customers:
    print(f"{customer.CustomerID}: {customer.Name}")

# Query with filters
active_customers = (
    service.entity("Customers")
    .filter("Country eq 'US' and Active eq true")
    .select("CustomerID", "Name", "Country")
    .top(10)
    .get()
)

# Create a new entity
new_customer = service.entity("Customers").create({
    "CustomerID": "CUST001",
    "Name": "ACME Corporation",
    "Country": "US",
    "Active": True
})

# Update an entity
service.entity("Customers('CUST001')").update({
    "Name": "ACME Corp International"
})

# Delete an entity
service.entity("Customers('CUST001')").delete()
```

### OData V2 (Gateway) Example

```python
from sap_odata import ODataClient

client = ODataClient(
    host="https://your-sap-system.com",
    username="your_user",
    password="your_password",
    client="100",
)

# Access a V2 service (no namespace needed)
service = client.service(name="ZSALESORDER_SRV", version="v2")

# Get sales orders
orders = (
    service.entity("SalesOrderSet")
    .filter("CreatedAt gt datetime'2024-01-01T00:00:00'")
    .expand("Items")
    .get()
)
```

### Working with Metadata

```python
# Get service metadata
metadata = service.metadata()

# List all entity sets
for entity_set in metadata.entity_sets:
    print(f"Entity: {entity_set.name}")
    for prop in entity_set.entity_type.properties:
        print(f"  - {prop.name}: {prop.type}")

# Check if entity exists
if metadata.has_entity("Customers"):
    customer_type = metadata.entity_type("Customers")
    print(f"Key properties: {customer_type.key_properties}")
```

### Batch Operations

```python
# Execute multiple operations in a single request
with service.batch() as batch:
    batch.get("Customers('CUST001')")
    batch.create("Customers", {"CustomerID": "CUST002", "Name": "New Corp"})
    batch.update("Customers('CUST003')", {"Name": "Updated Name"})
    
results = batch.execute()
```

## 📖 Documentation

Full documentation is available at [sap-odata-python.readthedocs.io](https://sap-odata-python.readthedocs.io).

- [Getting Started](https://sap-odata-python.readthedocs.io/en/latest/getting-started/)
- [API Reference](https://sap-odata-python.readthedocs.io/en/latest/api/)
- [Examples](https://sap-odata-python.readthedocs.io/en/latest/examples/)
- [V2 vs V4 Differences](https://sap-odata-python.readthedocs.io/en/latest/v2-vs-v4/)

## 🆚 Comparison with pyodata

| Feature | sap-odata-python | pyodata |
|---------|------------------|---------|
| OData V2 Support | ✅ | ✅ |
| OData V4 Support | ✅ | ❌ |
| SAP-specific optimizations | ✅ | ⚠️ Limited |
| Auto CSRF handling | ✅ | ❌ Manual |
| Query builder | ✅ | ✅ |
| Metadata parsing | ✅ | ✅ |
| Batch operations | ✅ | ✅ |
| Async support | ✅ | ❌ |
| Response normalization | ✅ | ❌ |
| Active maintenance | ✅ | ✅ |

## 🔧 Advanced Configuration

```python
from sap_odata import ODataClient, ODataConfig

# Advanced configuration
config = ODataConfig(
    timeout=120,
    verify_ssl=True,
    max_retries=3,
    retry_delay=1.0,
    csrf_token_refresh=True,
)

client = ODataClient(
    host="https://your-sap-system.com",
    username="your_user",
    password="your_password",
    client="100",
    config=config,
)
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by [pyodata](https://github.com/SAP/python-pyodata) by SAP
- SAP OData documentation and specifications
- The Python community

## 📞 Support

- 📧 Create an [issue](https://github.com/vaibhavgoel-github-1986/sap-odata-python/issues)
- 💬 Start a [discussion](https://github.com/vaibhavgoel-github-1986/sap-odata-python/discussions)

---

Made with ❤️ for the SAP developer community
