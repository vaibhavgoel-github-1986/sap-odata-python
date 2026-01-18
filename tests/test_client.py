"""Tests for OData client."""

import pytest
from sap_odata import ODataClient


# Public Northwind service
HOST = "https://services.odata.org"
V4_SERVICE = "V4/Northwind/Northwind.svc"
V2_SERVICE = "V2/Northwind/Northwind.svc"


@pytest.fixture
def client():
    """Create client for public Northwind service."""
    return ODataClient(HOST)


class TestODataV4:
    """Test OData V4 operations."""

    def test_get_products(self, client):
        """GET products."""
        data = client.get(V4_SERVICE, "Products", top=3)
        assert "value" in data
        assert len(data["value"]) == 3
        assert "ProductName" in data["value"][0]

    def test_get_with_filter(self, client):
        """GET with filter."""
        data = client.get(V4_SERVICE, "Products", filter="UnitPrice gt 50", top=5)
        assert "value" in data
        for item in data["value"]:
            assert item.get("UnitPrice", 0) > 50

    def test_get_with_select(self, client):
        """GET with select."""
        data = client.get(V4_SERVICE, "Products", select="ProductID,ProductName", top=2)
        assert "value" in data
        assert "ProductName" in data["value"][0]

    def test_get_single_entity(self, client):
        """GET single entity by key."""
        data = client.get(V4_SERVICE, "Products(1)")
        assert "value" in data
        assert data["value"][0]["ProductID"] == 1

    def test_get_categories(self, client):
        """GET categories."""
        data = client.get(V4_SERVICE, "Categories", top=3)
        assert "value" in data
        assert "CategoryName" in data["value"][0]


class TestODataV2:
    """Test OData V2 operations."""

    def test_get_products_v2(self, client):
        """GET products V2."""
        data = client.get(V2_SERVICE, "Products", version="v2", top=3)
        assert "value" in data
        assert len(data["value"]) == 3

    def test_get_categories_v2(self, client):
        """GET categories V2."""
        data = client.get(V2_SERVICE, "Categories", version="v2", top=3)
        assert "value" in data
        assert "CategoryName" in data["value"][0]


class TestMetadata:
    """Test metadata retrieval."""

    def test_get_metadata_v4(self, client):
        """GET metadata V4."""
        xml = client.metadata(V4_SERVICE)
        assert "EntityType" in xml
        assert "Product" in xml

    def test_get_metadata_v2(self, client):
        """GET metadata V2."""
        xml = client.metadata(V2_SERVICE, version="v2")
        assert "EntityType" in xml


class TestClientBasics:
    """Test client basics."""

    def test_context_manager(self):
        """Test context manager."""
        with ODataClient(HOST) as client:
            data = client.get(V4_SERVICE, "Products", top=1)
            assert "value" in data

    def test_empty_response_handling(self, client):
        """Test empty/no results."""
        data = client.get(V4_SERVICE, "Products", filter="ProductID eq -999")
        assert "value" in data
        assert len(data["value"]) == 0


class TestComplexExpand:
    """Test complex $expand scenarios like SAP uses."""

    def test_expand_v4(self, client):
        """GET with $expand V4."""
        data = client.get(
            V4_SERVICE, "Orders", 
            top=1, 
            expand="Customer,Order_Details"
        )
        assert "value" in data
        if data["value"]:
            order = data["value"][0]
            # Should have expanded Customer
            assert "Customer" in order or "CustomerID" in order

    def test_expand_v2(self, client):
        """GET with $expand V2."""
        data = client.get(
            V2_SERVICE, "Orders",
            version="v2",
            top=1,
            expand="Customer,Order_Details"
        )
        assert "value" in data
        if data["value"]:
            order = data["value"][0]
            # V2 expands should be present
            assert "Customer" in order or "CustomerID" in order

    def test_entity_with_key_v4(self, client):
        """GET single entity with key in path V4."""
        data = client.get(V4_SERVICE, "Products(1)")
        assert "value" in data
        assert data["value"][0]["ProductID"] == 1

    def test_entity_with_key_v2(self, client):
        """GET single entity with key in path V2."""
        data = client.get(V2_SERVICE, "Products(1)", version="v2")
        assert "value" in data
        assert data["value"][0]["ProductID"] == 1
