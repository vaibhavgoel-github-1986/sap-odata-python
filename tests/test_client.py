"""
Tests for SAPODataClient - Main client functionality.

Uses public Northwind OData services for real integration tests:
- V4: https://services.odata.org/V4/Northwind/Northwind.svc/
- V2: https://services.odata.org/V2/Northwind/Northwind.svc/
"""

import pytest
from sap_odata import SAPODataClient
from sap_odata.response import ODataResponse


class TestClientInitialization:
    """Test client initialization."""
    
    def test_create_client_no_auth(self):
        """Test creating client without authentication."""
        client = SAPODataClient(
            host="https://services.odata.org",
            username="",
            password="",
            is_sap=False,
        )
        assert client.host == "https://services.odata.org"
        assert client.is_sap is False
    
    def test_create_client_sap_mode(self):
        """Test creating client in SAP mode."""
        client = SAPODataClient(
            host="https://example.sap.com",
            username="",
            password="",
            client="100",
        )
        assert client.is_sap is True
        assert client.client == "100"
    
    def test_host_trailing_slash_removed(self):
        """Test that trailing slash is removed from host."""
        client = SAPODataClient(
            host="https://services.odata.org/",
            username="",
            password="",
            is_sap=False,
        )
        assert client.host == "https://services.odata.org"


class TestODataV4Operations:
    """Test OData V4 operations using Northwind service."""
    
    def test_get_products(self, v4_client):
        """Test GET request for products."""
        response = v4_client.call_odata(
            http_method="GET",
            service_name="V4/Northwind/Northwind.svc",
            entity_name="Products",
            odata_version="v4",
            query_parameters={"$top": 5}
        )
        
        assert response.is_success
        assert len(response.value) > 0
        assert "ProductID" in response.value[0]
        assert "ProductName" in response.value[0]
    
    def test_get_with_filter(self, v4_client):
        """Test GET with $filter parameter."""
        response = v4_client.call_odata(
            http_method="GET",
            service_name="V4/Northwind/Northwind.svc",
            entity_name="Products",
            odata_version="v4",
            query_parameters={
                "$filter": "UnitPrice gt 20",
                "$top": 5
            }
        )
        
        assert response.is_success
        for product in response.value:
            assert product.get("UnitPrice", 0) > 20
    
    def test_get_with_select(self, v4_client):
        """Test GET with $select parameter."""
        response = v4_client.call_odata(
            http_method="GET",
            service_name="V4/Northwind/Northwind.svc",
            entity_name="Products",
            odata_version="v4",
            query_parameters={
                "$select": "ProductID,ProductName",
                "$top": 3
            }
        )
        
        assert response.is_success
        # Should only have selected fields (plus OData metadata)
        product = response.first
        assert "ProductID" in product
        assert "ProductName" in product
    
    def test_get_with_orderby(self, v4_client):
        """Test GET with $orderby parameter."""
        response = v4_client.call_odata(
            http_method="GET",
            service_name="V4/Northwind/Northwind.svc",
            entity_name="Products",
            odata_version="v4",
            query_parameters={
                "$orderby": "ProductName asc",
                "$top": 5
            }
        )
        
        assert response.is_success
        names = [p["ProductName"] for p in response.value]
        assert names == sorted(names)
    
    def test_get_single_entity(self, v4_client):
        """Test GET single entity by key."""
        response = v4_client.call_odata(
            http_method="GET",
            service_name="V4/Northwind/Northwind.svc",
            entity_name="Products(1)",
            odata_version="v4"
        )
        
        assert response.is_success
        assert response.first["ProductID"] == 1
    
    def test_get_categories(self, v4_client):
        """Test GET categories."""
        response = v4_client.call_odata(
            http_method="GET",
            service_name="V4/Northwind/Northwind.svc",
            entity_name="Categories",
            odata_version="v4",
            query_parameters={"$top": 3}
        )
        
        assert response.is_success
        assert len(response.value) > 0
        assert "CategoryName" in response.first


class TestODataV2Operations:
    """Test OData V2 operations using Northwind service."""
    
    def test_get_products_v2(self, v2_client):
        """Test GET request for products (V2)."""
        response = v2_client.call_odata(
            http_method="GET",
            service_name="V2/Northwind/Northwind.svc",
            entity_name="Products",
            odata_version="v2",
            query_parameters={"$top": 5}
        )
        
        assert response.is_success
        assert len(response.value) > 0
        assert "ProductID" in response.value[0]
    
    def test_get_with_filter_v2(self, v2_client):
        """Test GET with $filter (V2)."""
        response = v2_client.call_odata(
            http_method="GET",
            service_name="V2/Northwind/Northwind.svc",
            entity_name="Products",
            odata_version="v2",
            query_parameters={
                "$filter": "UnitPrice gt 20",
                "$top": 5
            }
        )
        
        assert response.is_success
    
    def test_get_with_expand_v2(self, v2_client):
        """Test GET with $expand (V2)."""
        response = v2_client.call_odata(
            http_method="GET",
            service_name="V2/Northwind/Northwind.svc",
            entity_name="Categories",
            odata_version="v2",
            query_parameters={
                "$expand": "Products",
                "$top": 2
            }
        )
        
        assert response.is_success
        # Categories should have Products expanded
        category = response.first
        assert "CategoryName" in category
    
    def test_v2_response_normalization(self, v2_client):
        """Test that V2 responses are normalized to V4 format."""
        response = v2_client.call_odata(
            http_method="GET",
            service_name="V2/Northwind/Northwind.svc",
            entity_name="Products",
            odata_version="v2",
            query_parameters={"$top": 3}
        )
        
        # Should have 'value' array like V4
        assert "value" in response.data
        assert isinstance(response.value, list)


class TestResponseObject:
    """Test ODataResponse functionality."""
    
    def test_response_iteration(self, v4_client):
        """Test iterating over response."""
        response = v4_client.call_odata(
            http_method="GET",
            service_name="V4/Northwind/Northwind.svc",
            entity_name="Products",
            odata_version="v4",
            query_parameters={"$top": 3}
        )
        
        count = 0
        for item in response:
            count += 1
            assert "ProductID" in item
        assert count == len(response)
    
    def test_response_first(self, v4_client):
        """Test getting first item."""
        response = v4_client.call_odata(
            http_method="GET",
            service_name="V4/Northwind/Northwind.svc",
            entity_name="Products",
            odata_version="v4",
            query_parameters={"$top": 5}
        )
        
        first = response.first
        assert first is not None
        assert first == response.value[0]
    
    def test_response_len(self, v4_client):
        """Test response length."""
        response = v4_client.call_odata(
            http_method="GET",
            service_name="V4/Northwind/Northwind.svc",
            entity_name="Products",
            odata_version="v4",
            query_parameters={"$top": 5}
        )
        
        assert len(response) == len(response.value)
    
    def test_response_is_success(self, v4_client):
        """Test is_success property."""
        response = v4_client.call_odata(
            http_method="GET",
            service_name="V4/Northwind/Northwind.svc",
            entity_name="Products",
            odata_version="v4",
            query_parameters={"$top": 1}
        )
        
        assert response.is_success is True
        assert 200 <= response.status_code < 300


class TestMetadata:
    """Test metadata operations."""
    
    def test_get_metadata_v4(self, v4_client):
        """Test getting V4 metadata."""
        xml = v4_client.get_metadata(
            service_name="V4/Northwind/Northwind.svc",
            odata_version="v4"
        )
        
        assert "<?xml" in xml or "<edmx:Edmx" in xml
        assert "EntityType" in xml
    
    def test_get_metadata_v2(self, v2_client):
        """Test getting V2 metadata."""
        xml = v2_client.get_metadata(
            service_name="V2/Northwind/Northwind.svc",
            odata_version="v2"
        )
        
        assert "<?xml" in xml or "<edmx:Edmx" in xml
        assert "EntityType" in xml
    
    def test_parse_metadata_v4(self, v4_client):
        """Test parsing V4 metadata."""
        metadata = v4_client.get_metadata(
            service_name="V4/Northwind/Northwind.svc",
            odata_version="v4",
            parse=True
        )
        
        assert len(metadata.entity_types) > 0
        
        # Find Product entity
        product_type = metadata.get_entity_type("Product")
        assert product_type is not None
        assert len(product_type.properties) > 0
        
        # Check key property
        product_id = product_type.get_property("ProductID")
        assert product_id is not None
        assert product_id.is_key is True
    
    def test_parse_metadata_v2(self, v2_client):
        """Test parsing V2 metadata."""
        metadata = v2_client.get_metadata(
            service_name="V2/Northwind/Northwind.svc",
            odata_version="v2",
            parse=True
        )
        
        assert len(metadata.entity_types) > 0
        assert metadata.odata_version == "v2"


class TestContextManager:
    """Test context manager usage."""
    
    def test_context_manager(self):
        """Test using client as context manager."""
        with SAPODataClient(
            host="https://services.odata.org",
            username="",
            password="",
            is_sap=False,
        ) as client:
            response = client.call_odata(
                http_method="GET",
                service_name="V4/Northwind/Northwind.svc",
                entity_name="Products",
                odata_version="v4",
                query_parameters={"$top": 1}
            )
            assert response.is_success


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_query_parameters(self, v4_client):
        """Test with empty query parameters."""
        response = v4_client.call_odata(
            http_method="GET",
            service_name="V4/Northwind/Northwind.svc",
            entity_name="Categories",
            odata_version="v4",
            query_parameters={}
        )
        
        assert response.is_success
    
    def test_none_query_parameters(self, v4_client):
        """Test with None query parameters."""
        response = v4_client.call_odata(
            http_method="GET",
            service_name="V4/Northwind/Northwind.svc",
            entity_name="Categories",
            odata_version="v4",
            query_parameters=None
        )
        
        assert response.is_success
    
    def test_invalid_entity_returns_error(self, v4_client):
        """Test that invalid entity raises error."""
        with pytest.raises(Exception):
            v4_client.call_odata(
                http_method="GET",
                service_name="V4/Northwind/Northwind.svc",
                entity_name="NonExistentEntity",
                odata_version="v4"
            )
