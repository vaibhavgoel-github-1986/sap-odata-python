"""Tests for OData client using public OData services.

Public Test Services:
- Northwind V4: https://services.odata.org/V4/Northwind/Northwind.svc
- Northwind V2: https://services.odata.org/V2/Northwind/Northwind.svc
- TripPin V4: https://services.odata.org/TripPinRESTierService (read-only)
"""

import pytest
from sap_odata import ODataClient


# Public OData services (non-SAP, so sap_mode=False)
HOST = "https://services.odata.org"
V4_SERVICE = "V4/Northwind/Northwind.svc"
V2_SERVICE = "V2/Northwind/Northwind.svc"
TRIPPIN_SERVICE = "TripPinRESTierService"


@pytest.fixture
def client():
    """Create client for public Northwind service (non-SAP mode)."""
    return ODataClient(HOST, sap_mode=False)


@pytest.fixture
def trippin_client():
    """Create client for TripPin service (non-SAP mode)."""
    return ODataClient(HOST, sap_mode=False)


class TestODataV4:
    """Test OData V4 operations - raw response format."""

    def test_get_products(self, client):
        """GET products - V4 returns {"value": [...]}."""
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
        """GET single entity by key - V4 returns entity directly (no "value")."""
        data = client.get(V4_SERVICE, "Products(1)")
        # Single entity: {"@odata.context": "...", "ProductID": 1, ...}
        assert "ProductID" in data
        assert data["ProductID"] == 1

    def test_get_categories(self, client):
        """GET categories."""
        data = client.get(V4_SERVICE, "Categories", top=3)
        assert "value" in data
        assert "CategoryName" in data["value"][0]

    def test_odata_context(self, client):
        """V4 responses include @odata.context."""
        data = client.get(V4_SERVICE, "Products", top=1)
        assert "@odata.context" in data


class TestODataV2:
    """Test OData V2 operations - raw response format."""

    def test_get_products_v2(self, client):
        """GET products V2 - returns {"d": [...]} or {"d": {"results": [...]}}."""
        data = client.get(V2_SERVICE, "Products", version="v2", top=3)
        assert "d" in data
        # V2 can return {"d": [...]} or {"d": {"results": [...]}}
        items = client.get_value(data, "v2")
        assert len(items) == 3

    def test_get_categories_v2(self, client):
        """GET categories V2."""
        data = client.get(V2_SERVICE, "Categories", version="v2", top=3)
        assert "d" in data
        items = client.get_value(data, "v2")
        assert "CategoryName" in items[0]

    def test_get_single_entity_v2(self, client):
        """GET single entity V2 - returns {"d": {...}}."""
        data = client.get(V2_SERVICE, "Products(1)", version="v2")
        # Single entity: {"d": {"ProductID": 1, ...}}
        assert "d" in data
        assert data["d"]["ProductID"] == 1


class TestHelperMethods:
    """Test helper methods for extracting data."""

    def test_get_value_v4(self, client):
        """get_value() extracts value array from V4 response."""
        data = client.get(V4_SERVICE, "Products", top=3)
        items = client.get_value(data, "v4")
        assert len(items) == 3
        assert "ProductName" in items[0]

    def test_get_value_v4_single(self, client):
        """get_value() handles V4 single entity response."""
        data = client.get(V4_SERVICE, "Products(1)")
        items = client.get_value(data, "v4")
        assert len(items) == 1
        assert items[0]["ProductID"] == 1

    def test_get_value_v2(self, client):
        """get_value() extracts results from V2 response."""
        data = client.get(V2_SERVICE, "Products", version="v2", top=3)
        items = client.get_value(data, "v2")
        assert len(items) == 3

    def test_get_value_v2_single(self, client):
        """get_value() handles V2 single entity response."""
        data = client.get(V2_SERVICE, "Products(1)", version="v2")
        items = client.get_value(data, "v2")
        assert len(items) == 1
        assert items[0]["ProductID"] == 1


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
        with ODataClient(HOST, sap_mode=False) as client:
            data = client.get(V4_SERVICE, "Products", top=1)
            assert "value" in data

    def test_empty_response_handling(self, client):
        """Test empty/no results."""
        data = client.get(V4_SERVICE, "Products", filter="ProductID eq -999")
        assert "value" in data
        assert len(data["value"]) == 0
    
    def test_sap_mode_default_true(self):
        """Default sap_mode should be True."""
        client = ODataClient("https://any-host.com")
        assert client.sap_mode is True
    
    def test_sap_mode_explicit_false(self):
        """Explicit sap_mode=False should be respected."""
        client = ODataClient("https://any-host.com", sap_mode=False)
        assert client.sap_mode is False


class TestComplexExpand:
    """Test complex $expand scenarios."""

    def test_expand_v4(self, client):
        """GET with $expand V4."""
        data = client.get(
            V4_SERVICE, "Orders", 
            top=1, 
            expand="Customer,Order_Details"
        )
        assert "value" in data

    def test_expand_v2(self, client):
        """GET with $expand V2."""
        data = client.get(
            V2_SERVICE, "Orders",
            version="v2",
            top=1,
            expand="Customer,Order_Details"
        )
        assert "d" in data

    def test_entity_with_key_v4(self, client):
        """GET single entity with key in path V4."""
        data = client.get(V4_SERVICE, "Products(1)")
        assert data["ProductID"] == 1

    def test_entity_with_key_v2(self, client):
        """GET single entity with key in path V2."""
        data = client.get(V2_SERVICE, "Products(1)", version="v2")
        assert data["d"]["ProductID"] == 1


class TestTripPin:
    """Test TripPin OData V4 service."""

    def test_get_people(self, trippin_client):
        """GET people from TripPin."""
        data = trippin_client.get(TRIPPIN_SERVICE, "People", top=3)
        assert "value" in data
        assert len(data["value"]) <= 3
        assert "FirstName" in data["value"][0]

    def test_get_airlines(self, trippin_client):
        """GET airlines from TripPin."""
        data = trippin_client.get(TRIPPIN_SERVICE, "Airlines")
        assert "value" in data
        assert "AirlineCode" in data["value"][0]

    def test_get_airports(self, trippin_client):
        """GET airports from TripPin."""
        data = trippin_client.get(TRIPPIN_SERVICE, "Airports", top=5)
        assert "value" in data
        assert "IcaoCode" in data["value"][0]

    def test_filter_people(self, trippin_client):
        """GET people with filter."""
        data = trippin_client.get(
            TRIPPIN_SERVICE, "People",
            filter="FirstName eq 'Russell'"
        )
        assert "value" in data
        if data["value"]:
            assert data["value"][0]["FirstName"] == "Russell"

    def test_single_person(self, trippin_client):
        """GET single person by key."""
        data = trippin_client.get(TRIPPIN_SERVICE, "People('russellwhyte')")
        # Single entity response
        assert "UserName" in data
        assert data["UserName"] == "russellwhyte"

    def test_expand_trips(self, trippin_client):
        """GET person with expanded trips."""
        data = trippin_client.get(
            TRIPPIN_SERVICE, "People('russellwhyte')",
            expand="Trips"
        )
        assert "UserName" in data


class TestValidation:
    """Test input validation."""

    def test_empty_service_raises_error(self, client):
        """Empty service name should raise error."""
        from sap_odata import ODataError
        with pytest.raises(ODataError, match="Service name is required"):
            client.get("", "Products")

    def test_empty_entity_raises_error(self, client):
        """Empty entity name should raise error."""
        from sap_odata import ODataError
        with pytest.raises(ODataError, match="Entity name is required"):
            client.get(V4_SERVICE, "")

    def test_invalid_version_raises_error(self, client):
        """Invalid version should raise error."""
        from sap_odata import ODataError
        with pytest.raises(ODataError, match="Invalid version"):
            client.get(V4_SERVICE, "Products", version="v3")

    def test_sap_v4_without_namespace_raises_error(self):
        """SAP V4 without namespace should raise error."""
        from sap_odata import ODataError
        sap_client = ODataClient("https://sap-server.com", sap_mode=True)
        with pytest.raises(ODataError, match="Namespace is required"):
            sap_client.get("zsd_my_service", "MyEntity", version="v4")

    def test_sap_v4_with_namespace_works(self):
        """SAP V4 with namespace should not raise ODataValidationError."""
        from sap_odata import ODataError, ODataConnectionError
        sap_client = ODataClient("https://fake-sap-server-xyz123.local", sap_mode=True)
        # Should pass validation but fail on connection (no real server)
        with pytest.raises((ODataConnectionError, ODataError)):
            sap_client.get("zsd_my_service", "MyEntity", version="v4", namespace="zsb_my_service")

    def test_sap_v2_without_namespace_works(self):
        """SAP V2 doesn't require namespace."""
        from sap_odata import ODataError, ODataConnectionError
        sap_client = ODataClient("https://fake-sap-server-xyz123.local", sap_mode=True)
        # Should pass validation but fail on connection (no real server)
        with pytest.raises((ODataConnectionError, ODataError)):
            sap_client.get("ZMY_SERVICE_SRV", "MyEntity", version="v2")
