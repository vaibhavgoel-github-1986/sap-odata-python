"""
Tests for Query Builder.
"""

import pytest
from unittest.mock import MagicMock, patch
from sap_odata.query import QueryBuilder


class TestQueryBuilder:
    """Tests for QueryBuilder class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_service = MagicMock()
        self.mock_service.version = "v4"
        self.query = QueryBuilder(self.mock_service, "Customers")
    
    def test_init(self):
        """Test query builder initialization."""
        assert self.query._entity_name == "Customers"
        assert self.query._filter is None
        assert self.query._select == []
        assert self.query._top is None
    
    def test_filter(self):
        """Test filter method."""
        result = self.query.filter("Country eq 'US'")
        
        assert result is self.query  # Returns self
        assert self.query._filter == "Country eq 'US'"
    
    def test_select_single(self):
        """Test select with single property."""
        self.query.select("Name")
        
        assert self.query._select == ["Name"]
    
    def test_select_multiple(self):
        """Test select with multiple properties."""
        self.query.select("Name", "Country", "Active")
        
        assert self.query._select == ["Name", "Country", "Active"]
    
    def test_expand(self):
        """Test expand method."""
        self.query.expand("Orders", "Addresses")
        
        assert self.query._expand == ["Orders", "Addresses"]
    
    def test_orderby(self):
        """Test orderby method."""
        self.query.orderby("Name asc")
        
        assert self.query._orderby == "Name asc"
    
    def test_top(self):
        """Test top method."""
        self.query.top(10)
        
        assert self.query._top == 10
    
    def test_skip(self):
        """Test skip method."""
        self.query.skip(20)
        
        assert self.query._skip == 20
    
    def test_count_v4(self):
        """Test count method for V4."""
        self.query.count()
        
        params = self.query._build_params()
        assert params.get("$count") == "true"
    
    def test_count_v2(self):
        """Test count method for V2."""
        self.mock_service.version = "v2"
        query = QueryBuilder(self.mock_service, "Customers")
        query.count()
        
        params = query._build_params()
        assert params.get("$inlinecount") == "allpages"
    
    def test_search(self):
        """Test search method."""
        self.query.search("Corporation")
        
        assert self.query._search == "Corporation"
    
    def test_custom(self):
        """Test custom parameter method."""
        self.query.custom("myParam", "myValue")
        
        params = self.query._build_params()
        assert params.get("myParam") == "myValue"
    
    def test_chaining(self):
        """Test method chaining."""
        result = (
            self.query
            .filter("Active eq true")
            .select("Name", "Country")
            .top(10)
            .orderby("Name asc")
        )
        
        assert result is self.query
        assert self.query._filter == "Active eq true"
        assert self.query._select == ["Name", "Country"]
        assert self.query._top == 10
        assert self.query._orderby == "Name asc"
    
    def test_build_params(self):
        """Test building query parameters."""
        self.query.filter("Active eq true")
        self.query.select("Name", "Country")
        self.query.expand("Orders")
        self.query.top(10)
        self.query.skip(5)
        self.query.orderby("Name desc")
        
        params = self.query._build_params()
        
        assert params["$filter"] == "Active eq true"
        assert params["$select"] == "Name,Country"
        assert params["$expand"] == "Orders"
        assert params["$top"] == 10
        assert params["$skip"] == 5
        assert params["$orderby"] == "Name desc"
    
    def test_get(self):
        """Test get method."""
        self.mock_service.execute_request.return_value = {
            "status_code": 200,
            "data": {
                "value": [
                    {"CustomerID": "C001", "Name": "Customer 1"},
                    {"CustomerID": "C002", "Name": "Customer 2"},
                ]
            }
        }
        
        results = self.query.get()
        
        assert len(results) == 2
        assert results[0]["CustomerID"] == "C001"
        self.mock_service.execute_request.assert_called_once()
    
    def test_get_single(self):
        """Test get_single method."""
        self.mock_service.execute_request.return_value = {
            "status_code": 200,
            "data": {
                "value": [{"CustomerID": "C001", "Name": "Customer 1"}]
            }
        }
        
        result = self.query.get_single()
        
        assert result["CustomerID"] == "C001"
    
    def test_get_single_empty(self):
        """Test get_single with no results."""
        self.mock_service.execute_request.return_value = {
            "status_code": 200,
            "data": {"value": []}
        }
        
        result = self.query.get_single()
        
        assert result is None
    
    def test_create(self):
        """Test create method."""
        self.mock_service.execute_request.return_value = {
            "status_code": 201,
            "data": {"CustomerID": "C001", "Name": "New Customer"}
        }
        
        data = {"CustomerID": "C001", "Name": "New Customer"}
        result = self.query.create(data)
        
        assert result["CustomerID"] == "C001"
        self.mock_service.execute_request.assert_called_with(
            method="POST",
            entity_path="Customers",
            json_body=data,
        )
    
    def test_update(self):
        """Test update method."""
        self.mock_service.execute_request.return_value = {
            "status_code": 200,
            "data": {"Name": "Updated Name"}
        }
        
        query = QueryBuilder(self.mock_service, "Customers('C001')")
        data = {"Name": "Updated Name"}
        result = query.update(data)
        
        self.mock_service.execute_request.assert_called_with(
            method="PATCH",
            entity_path="Customers('C001')",
            json_body=data,
        )
    
    def test_delete(self):
        """Test delete method."""
        self.mock_service.execute_request.return_value = {
            "status_code": 204,
            "data": None
        }
        
        query = QueryBuilder(self.mock_service, "Customers('C001')")
        result = query.delete()
        
        assert result is True
        self.mock_service.execute_request.assert_called_with(
            method="DELETE",
            entity_path="Customers('C001')",
        )
