"""
Tests for ODataResponse class.
"""

import pytest
from sap_odata.response import ODataResponse


class TestODataResponse:
    """Test ODataResponse functionality."""
    
    def test_basic_response(self):
        """Test basic response creation."""
        response = ODataResponse(
            status_code=200,
            data={"value": [{"id": 1}, {"id": 2}]},
        )
        
        assert response.status_code == 200
        assert len(response.value) == 2
        assert response.is_success is True
        assert response.is_empty is False
    
    def test_empty_response(self):
        """Test empty response."""
        response = ODataResponse(
            status_code=200,
            data={"value": []},
        )
        
        assert response.is_empty is True
        assert response.first is None
        assert len(response) == 0
    
    def test_first_property(self):
        """Test first property."""
        response = ODataResponse(
            status_code=200,
            data={"value": [{"name": "first"}, {"name": "second"}]},
        )
        
        assert response.first["name"] == "first"
    
    def test_iteration(self):
        """Test iterating over response."""
        items = [{"id": 1}, {"id": 2}, {"id": 3}]
        response = ODataResponse(
            status_code=200,
            data={"value": items},
        )
        
        result = list(response)
        assert result == items
    
    def test_len(self):
        """Test len() on response."""
        response = ODataResponse(
            status_code=200,
            data={"value": [{"id": 1}, {"id": 2}, {"id": 3}]},
        )
        
        assert len(response) == 3
    
    def test_getitem_index(self):
        """Test indexing response."""
        response = ODataResponse(
            status_code=200,
            data={"value": [{"id": 1}, {"id": 2}, {"id": 3}]},
        )
        
        assert response[0]["id"] == 1
        assert response[1]["id"] == 2
        assert response[2]["id"] == 3
    
    def test_is_success_2xx(self):
        """Test is_success for various status codes."""
        for code in [200, 201, 204]:
            response = ODataResponse(status_code=code, data={"value": []})
            assert response.is_success is True
    
    def test_is_success_non_2xx(self):
        """Test is_success for error status codes."""
        for code in [400, 401, 404, 500]:
            response = ODataResponse(status_code=code, data={"value": []})
            assert response.is_success is False
    
    def test_has_more_with_next_link(self):
        """Test has_more with next_link."""
        response = ODataResponse(
            status_code=200,
            data={"value": [{"id": 1}]},
            next_link="http://example.com/next"
        )
        
        assert response.has_more is True
    
    def test_has_more_without_next_link(self):
        """Test has_more without next_link."""
        response = ODataResponse(
            status_code=200,
            data={"value": [{"id": 1}]},
        )
        
        assert response.has_more is False
    
    def test_count(self):
        """Test count property."""
        response = ODataResponse(
            status_code=200,
            data={"value": [{"id": 1}], "@odata.count": 100},
            count=100,
        )
        
        assert response.count == 100
    
    def test_to_dict(self):
        """Test to_dict method."""
        response = ODataResponse(
            status_code=200,
            data={"value": [{"id": 1}]},
            count=1,
            next_link=None,
        )
        
        d = response.to_dict()
        assert d["status_code"] == 200
        assert d["is_success"] is True
        assert d["record_count"] == 1
    
    def test_bool_truthy(self):
        """Test truthiness of response with data."""
        response = ODataResponse(
            status_code=200,
            data={"value": [{"id": 1}]},
        )
        
        assert bool(response) is True
    
    def test_bool_falsy_empty(self):
        """Test truthiness of empty response."""
        response = ODataResponse(
            status_code=200,
            data={"value": []},
        )
        
        assert bool(response) is False
    
    def test_bool_falsy_error(self):
        """Test truthiness of error response."""
        response = ODataResponse(
            status_code=404,
            data={"value": []},
        )
        
        assert bool(response) is False
    
    def test_repr(self):
        """Test string representation."""
        response = ODataResponse(
            status_code=200,
            data={"value": [{"id": 1}, {"id": 2}]},
        )
        
        repr_str = repr(response)
        assert "200" in repr_str
        assert "2" in repr_str  # records count
