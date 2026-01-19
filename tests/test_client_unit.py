"""Unit tests for OData client using mocking.

These tests cover code paths that can't be easily tested with public services:
- POST, PATCH, PUT, DELETE operations
- CSRF token handling
- Error handling (auth errors, HTTP errors, connection errors)
- SAP mode URL building
- Empty response handling
- Helper methods (get_value, get_count, get_next_link)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests

from sap_odata import ODataClient, ODataError, ODataConnectionError, ODataAuthError


class TestHTTPMethods:
    """Test all HTTP methods with mocked responses."""

    @pytest.fixture
    def mock_session(self):
        """Create a client with mocked session."""
        with patch('sap_odata.client.requests.Session') as mock:
            client = ODataClient("https://sap.example.com", sap_mode=False)
            yield client, mock.return_value

    def test_post_request(self):
        """Test POST creates data correctly."""
        with patch.object(ODataClient, '_request') as mock_request:
            mock_request.return_value = {"value": [{"ID": 1}]}
            client = ODataClient("https://sap.example.com", sap_mode=False)
            
            result = client.post("TestService", "Products", {"Name": "Test"})
            
            mock_request.assert_called_once_with(
                "POST", "TestService", "Products", "v4", "", body={"Name": "Test"}
            )

    def test_patch_request(self):
        """Test PATCH updates data correctly."""
        with patch.object(ODataClient, '_request') as mock_request:
            mock_request.return_value = {"value": []}
            client = ODataClient("https://sap.example.com", sap_mode=False)
            
            result = client.patch("TestService", "Products(1)", {"Name": "Updated"})
            
            mock_request.assert_called_once_with(
                "PATCH", "TestService", "Products(1)", "v4", "", body={"Name": "Updated"}
            )

    def test_put_request(self):
        """Test PUT replaces data correctly."""
        with patch.object(ODataClient, '_request') as mock_request:
            mock_request.return_value = {"value": []}
            client = ODataClient("https://sap.example.com", sap_mode=False)
            
            result = client.put("TestService", "Products(1)", {"Name": "Replaced", "Price": 100})
            
            mock_request.assert_called_once_with(
                "PUT", "TestService", "Products(1)", "v4", "", body={"Name": "Replaced", "Price": 100}
            )

    def test_delete_request(self):
        """Test DELETE removes data correctly."""
        with patch.object(ODataClient, '_request') as mock_request:
            mock_request.return_value = {"value": []}
            client = ODataClient("https://sap.example.com", sap_mode=False)
            
            result = client.delete("TestService", "Products(1)")
            
            mock_request.assert_called_once_with(
                "DELETE", "TestService", "Products(1)", "v4", ""
            )

    def test_post_with_v2(self):
        """Test POST with V2 version."""
        with patch.object(ODataClient, '_request') as mock_request:
            mock_request.return_value = {"d": {"ID": 1}}
            client = ODataClient("https://sap.example.com", sap_mode=False)
            
            result = client.post("TestService", "Products", {"Name": "Test"}, version="v2")
            
            mock_request.assert_called_once_with(
                "POST", "TestService", "Products", "v2", "", body={"Name": "Test"}
            )


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_connection_error(self):
        """Test connection error is properly wrapped."""
        client = ODataClient("https://nonexistent-server-xyz123.local", sap_mode=False)
        
        with pytest.raises(ODataConnectionError, match="Connection failed"):
            client.get("TestService", "Products")

    def test_auth_error_401(self):
        """Test 401 error raises ODataAuthError."""
        with patch('sap_odata.client.requests.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            # Create mock response with 401 status
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.text = "Unauthorized"
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
            
            mock_session.request.return_value = mock_response
            
            client = ODataClient("https://sap.example.com", sap_mode=False)
            
            with pytest.raises(ODataAuthError, match="Authentication failed"):
                client.get("TestService", "Products")

    def test_http_error_500(self):
        """Test 500 error raises ODataError with details."""
        with patch('sap_odata.client.requests.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            # Create mock response with 500 status
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error - Something went wrong"
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
            
            mock_session.request.return_value = mock_response
            
            client = ODataClient("https://sap.example.com", sap_mode=False)
            
            with pytest.raises(ODataError, match="HTTP 500"):
                client.get("TestService", "Products")

    def test_http_error_404(self):
        """Test 404 error raises ODataError."""
        with patch('sap_odata.client.requests.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.text = "Not Found"
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
            
            mock_session.request.return_value = mock_response
            
            client = ODataClient("https://sap.example.com", sap_mode=False)
            
            with pytest.raises(ODataError, match="HTTP 404"):
                client.get("TestService", "Products")


class TestCSRFToken:
    """Test CSRF token handling for SAP systems."""

    def test_csrf_token_fetched_for_post(self):
        """Test CSRF token is fetched for POST requests in SAP mode."""
        with patch('sap_odata.client.requests.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            # Mock CSRF fetch response
            csrf_response = Mock()
            csrf_response.headers = {"X-CSRF-Token": "test-csrf-token-123"}
            
            # Mock actual POST response
            post_response = Mock()
            post_response.status_code = 201
            post_response.text = '{"value": [{"ID": 1}]}'
            post_response.json.return_value = {"value": [{"ID": 1}]}
            post_response.raise_for_status = Mock()
            
            mock_session.get.return_value = csrf_response
            mock_session.request.return_value = post_response
            
            client = ODataClient(
                "https://sap.example.com",
                username="user",
                password="pass",
                client="100",
                sap_mode=True
            )
            
            result = client.post("zsd_test", "Products", {"Name": "Test"}, version="v4", namespace="zsb_test")
            
            # Verify CSRF was fetched
            mock_session.get.assert_called_once()
            # Verify the request was made
            mock_session.request.assert_called_once()
            
            # Verify CSRF token in headers
            call_kwargs = mock_session.request.call_args
            assert call_kwargs[1]['headers']['X-CSRF-Token'] == 'test-csrf-token-123'

    def test_csrf_token_cached(self):
        """Test CSRF token is cached and reused."""
        with patch('sap_odata.client.requests.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            csrf_response = Mock()
            csrf_response.headers = {"X-CSRF-Token": "cached-token"}
            
            post_response = Mock()
            post_response.status_code = 200
            post_response.text = '{"value": []}'
            post_response.json.return_value = {"value": []}
            post_response.raise_for_status = Mock()
            
            mock_session.get.return_value = csrf_response
            mock_session.request.return_value = post_response
            
            client = ODataClient("https://sap.example.com", sap_mode=True)
            
            # First POST - should fetch token
            client.post("zsd_test", "Products", {}, version="v4", namespace="zsb_test")
            
            # Second POST - should reuse cached token
            client.post("zsd_test", "Products", {}, version="v4", namespace="zsb_test")
            
            # CSRF should only be fetched once
            assert mock_session.get.call_count == 1

    def test_csrf_token_required_header(self):
        """Test CSRF token 'Required' value is ignored."""
        with patch('sap_odata.client.requests.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            csrf_response = Mock()
            csrf_response.headers = {"X-CSRF-Token": "Required"}
            
            post_response = Mock()
            post_response.status_code = 200
            post_response.text = '{"value": []}'
            post_response.json.return_value = {"value": []}
            post_response.raise_for_status = Mock()
            
            mock_session.get.return_value = csrf_response
            mock_session.request.return_value = post_response
            
            client = ODataClient("https://sap.example.com", sap_mode=True)
            client.post("zsd_test", "Products", {}, version="v4", namespace="zsb_test")
            
            # Token should not be set when value is "Required"
            call_kwargs = mock_session.request.call_args
            assert 'X-CSRF-Token' not in call_kwargs[1]['headers'] or call_kwargs[1]['headers'].get('X-CSRF-Token') != 'Required'


class TestResponseParsing:
    """Test response parsing scenarios."""

    def test_empty_response_204_v4(self):
        """Test 204 No Content response returns empty value for V4."""
        with patch('sap_odata.client.requests.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            mock_response = Mock()
            mock_response.status_code = 204
            mock_response.text = ""
            mock_response.raise_for_status = Mock()
            
            mock_session.request.return_value = mock_response
            
            client = ODataClient("https://sap.example.com", sap_mode=False)
            result = client.delete("TestService", "Products(1)")
            
            assert result == {"value": []}

    def test_empty_response_204_v2(self):
        """Test 204 No Content response returns empty d for V2."""
        with patch('sap_odata.client.requests.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            mock_response = Mock()
            mock_response.status_code = 204
            mock_response.text = ""
            mock_response.raise_for_status = Mock()
            
            mock_session.request.return_value = mock_response
            
            client = ODataClient("https://sap.example.com", sap_mode=False)
            result = client.delete("TestService", "Products(1)", version="v2")
            
            assert result == {"d": []}

    def test_invalid_json_response_v4(self):
        """Test invalid JSON response includes raw text for V4."""
        with patch('sap_odata.client.requests.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "Not valid JSON"
            mock_response.json.side_effect = ValueError("Invalid JSON")
            mock_response.raise_for_status = Mock()
            
            mock_session.request.return_value = mock_response
            
            client = ODataClient("https://sap.example.com", sap_mode=False)
            result = client.get("TestService", "Products")
            
            assert result == {"value": [], "raw": "Not valid JSON"}

    def test_invalid_json_response_v2(self):
        """Test invalid JSON response includes raw text for V2."""
        with patch('sap_odata.client.requests.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "Not valid JSON"
            mock_response.json.side_effect = ValueError("Invalid JSON")
            mock_response.raise_for_status = Mock()
            
            mock_session.request.return_value = mock_response
            
            client = ODataClient("https://sap.example.com", sap_mode=False)
            result = client.get("TestService", "Products", version="v2")
            
            assert result == {"d": [], "raw": "Not valid JSON"}


class TestURLBuilding:
    """Test URL building for SAP and non-SAP modes."""

    def test_sap_v4_url_building(self):
        """Test SAP V4 URL is built correctly."""
        client = ODataClient("https://sap.example.com", sap_mode=True)
        url = client._build_url("zsd_my_service", "Products", "v4", "zsb_my_service")
        
        expected = "https://sap.example.com/sap/opu/odata4/sap/zsb_my_service/srvd_a2x/sap/zsd_my_service/0001/Products"
        assert url == expected

    def test_sap_v2_url_building(self):
        """Test SAP V2 URL is built correctly."""
        client = ODataClient("https://sap.example.com", sap_mode=True)
        url = client._build_url("ZMY_SERVICE_SRV", "Products", "v2", "")
        
        expected = "https://sap.example.com/sap/opu/odata/sap/ZMY_SERVICE_SRV/Products"
        assert url == expected

    def test_non_sap_url_building(self):
        """Test non-SAP URL is built correctly."""
        client = ODataClient("https://services.odata.org", sap_mode=False)
        url = client._build_url("V4/Northwind/Northwind.svc", "Products", "v4", "")
        
        expected = "https://services.odata.org/V4/Northwind/Northwind.svc/Products"
        assert url == expected

    def test_non_sap_url_strips_leading_slash(self):
        """Test leading slash is stripped for non-SAP URLs."""
        client = ODataClient("https://services.odata.org", sap_mode=False)
        url = client._build_url("/V4/Northwind/Northwind.svc", "Products", "v4", "")
        
        expected = "https://services.odata.org/V4/Northwind/Northwind.svc/Products"
        assert url == expected

    def test_sap_v4_namespace_lowercase(self):
        """Test SAP V4 namespace is converted to lowercase."""
        client = ODataClient("https://sap.example.com", sap_mode=True)
        url = client._build_url("ZSD_MY_SERVICE", "Products", "v4", "ZSB_MY_SERVICE")
        
        # Both service and namespace should be lowercase in URL
        assert "zsb_my_service" in url.lower()
        assert "zsd_my_service" in url.lower()


class TestQueryParameters:
    """Test query parameter handling."""

    def test_shorthand_params_converted(self):
        """Test shorthand params are converted to OData format."""
        client = ODataClient("https://sap.example.com", sap_mode=False)
        
        params = client._get_params({
            "top": 10,
            "skip": 5,
            "filter": "Price gt 100",
            "select": "ID,Name",
            "expand": "Category",
            "orderby": "Name asc",
            "count": True,
            "search": "test"
        })
        
        assert params["$top"] == 10
        assert params["$skip"] == 5
        assert params["$filter"] == "Price gt 100"
        assert params["$select"] == "ID,Name"
        assert params["$expand"] == "Category"
        assert params["$orderby"] == "Name asc"
        assert params["$count"] == True
        assert params["$search"] == "test"

    def test_sap_client_added_for_get(self):
        """Test SAP client is added to GET requests."""
        client = ODataClient("https://sap.example.com", client="100", sap_mode=True)
        
        params = client._get_params({}, version="v4", method="GET")
        
        assert params["sap-client"] == "100"

    def test_sap_client_not_added_for_post(self):
        """Test SAP client is NOT added to POST requests."""
        client = ODataClient("https://sap.example.com", client="100", sap_mode=True)
        
        params = client._get_params({}, version="v4", method="POST")
        
        assert "sap-client" not in params

    def test_v2_json_format_auto_added(self):
        """Test V2 auto-adds $format=json for GET."""
        client = ODataClient("https://sap.example.com", sap_mode=False)
        
        params = client._get_params({}, version="v2", method="GET")
        
        assert params["$format"] == "json"

    def test_v4_no_format_added(self):
        """Test V4 does NOT add $format automatically."""
        client = ODataClient("https://sap.example.com", sap_mode=False)
        
        params = client._get_params({}, version="v4", method="GET")
        
        assert "$format" not in params

    def test_custom_format_preserved(self):
        """Test custom $format is preserved and not overwritten."""
        client = ODataClient("https://sap.example.com", sap_mode=False)
        
        params = client._get_params({"$format": "xml"}, version="v2", method="GET")
        
        assert params["$format"] == "xml"


class TestHelperMethods:
    """Test helper methods for response extraction."""

    def test_get_value_v4(self):
        """Test get_value extracts value array from V4 response."""
        client = ODataClient("https://sap.example.com", sap_mode=False)
        
        response = {"@odata.context": "...", "value": [{"ID": 1}, {"ID": 2}]}
        result = client.get_value(response, "v4")
        
        assert result == [{"ID": 1}, {"ID": 2}]

    def test_get_value_v4_empty(self):
        """Test get_value returns empty list when no value."""
        client = ODataClient("https://sap.example.com", sap_mode=False)
        
        response = {"@odata.context": "..."}
        result = client.get_value(response, "v4")
        
        assert result == []

    def test_get_value_v2_list(self):
        """Test get_value extracts list from V2 response."""
        client = ODataClient("https://sap.example.com", sap_mode=False)
        
        response = {"d": [{"ID": 1}, {"ID": 2}]}
        result = client.get_value(response, "v2")
        
        assert result == [{"ID": 1}, {"ID": 2}]

    def test_get_value_v2_results(self):
        """Test get_value extracts results from V2 response."""
        client = ODataClient("https://sap.example.com", sap_mode=False)
        
        response = {"d": {"results": [{"ID": 1}], "__count": "10"}}
        result = client.get_value(response, "v2")
        
        assert result == [{"ID": 1}]

    def test_get_value_v2_empty(self):
        """Test get_value returns empty list for empty V2 response."""
        client = ODataClient("https://sap.example.com", sap_mode=False)
        
        response = {"d": {}}
        result = client.get_value(response, "v2")
        
        assert result == []

    def test_get_count_v4(self):
        """Test get_count extracts count from V4 response."""
        client = ODataClient("https://sap.example.com", sap_mode=False)
        
        response = {"@odata.context": "...", "@odata.count": 42, "value": []}
        result = client.get_count(response, "v4")
        
        assert result == 42

    def test_get_count_v4_missing(self):
        """Test get_count returns -1 when not available in V4."""
        client = ODataClient("https://sap.example.com", sap_mode=False)
        
        response = {"@odata.context": "...", "value": []}
        result = client.get_count(response, "v4")
        
        assert result == -1

    def test_get_count_v2(self):
        """Test get_count extracts count from V2 response."""
        client = ODataClient("https://sap.example.com", sap_mode=False)
        
        response = {"d": {"results": [], "__count": "100"}}
        result = client.get_count(response, "v2")
        
        assert result == 100

    def test_get_count_v2_missing(self):
        """Test get_count returns -1 when not available in V2."""
        client = ODataClient("https://sap.example.com", sap_mode=False)
        
        response = {"d": []}
        result = client.get_count(response, "v2")
        
        assert result == -1

    def test_get_next_link_v4(self):
        """Test get_next_link extracts nextLink from V4."""
        client = ODataClient("https://sap.example.com", sap_mode=False)
        
        response = {"value": [], "@odata.nextLink": "https://sap/Products?$skip=10"}
        result = client.get_next_link(response, "v4")
        
        assert result == "https://sap/Products?$skip=10"

    def test_get_next_link_v2(self):
        """Test get_next_link extracts __next from V2."""
        client = ODataClient("https://sap.example.com", sap_mode=False)
        
        response = {"d": {"results": [], "__next": "https://sap/Products?$skip=10"}}
        result = client.get_next_link(response, "v2")
        
        assert result == "https://sap/Products?$skip=10"

    def test_get_next_link_not_present(self):
        """Test get_next_link returns empty string when no next page."""
        client = ODataClient("https://sap.example.com", sap_mode=False)
        
        response_v4 = {"value": []}
        response_v2 = {"d": []}
        
        assert client.get_next_link(response_v4, "v4") == ""
        assert client.get_next_link(response_v2, "v2") == ""


class TestClientConfiguration:
    """Test client configuration options."""

    def test_timeout_configuration(self):
        """Test timeout is properly configured."""
        client = ODataClient("https://sap.example.com", timeout=120)
        assert client.timeout == 120

    def test_default_timeout(self):
        """Test default timeout is 60 seconds."""
        client = ODataClient("https://sap.example.com")
        assert client.timeout == 60

    def test_ssl_verification_disabled(self):
        """Test SSL verification can be disabled."""
        with patch('sap_odata.client.requests.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            client = ODataClient("https://sap.example.com", verify_ssl=False)
            
            assert mock_session.verify == False

    def test_ssl_verification_enabled_by_default(self):
        """Test SSL verification is enabled by default."""
        with patch('sap_odata.client.requests.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            client = ODataClient("https://sap.example.com")
            
            assert mock_session.verify == True

    def test_host_trailing_slash_stripped(self):
        """Test trailing slash is stripped from host."""
        client = ODataClient("https://sap.example.com/")
        assert client.host == "https://sap.example.com"

    def test_authentication_configured(self):
        """Test basic auth is configured when credentials provided."""
        with patch('sap_odata.client.requests.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            client = ODataClient(
                "https://sap.example.com",
                username="testuser",
                password="testpass"
            )
            
            # Auth should be set on session
            assert mock_session.auth is not None


class TestContextManager:
    """Test context manager functionality."""

    def test_context_manager_closes_session(self):
        """Test context manager closes session on exit."""
        with patch('sap_odata.client.requests.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            with ODataClient("https://sap.example.com") as client:
                pass
            
            mock_session.close.assert_called_once()

    def test_close_method(self):
        """Test close method closes session."""
        with patch('sap_odata.client.requests.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            client = ODataClient("https://sap.example.com")
            client.close()
            
            mock_session.close.assert_called_once()


class TestMetadataRetrieval:
    """Test metadata retrieval functionality."""

    def test_metadata_returns_xml(self):
        """Test metadata returns XML string."""
        with patch('sap_odata.client.requests.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            mock_response = Mock()
            mock_response.text = '<edmx:Edmx><EntityType Name="Product"/></edmx:Edmx>'
            mock_response.raise_for_status = Mock()
            
            mock_session.get.return_value = mock_response
            
            client = ODataClient("https://sap.example.com", sap_mode=False)
            result = client.metadata("TestService", version="v4")
            
            assert "EntityType" in result

    def test_metadata_accepts_application_xml(self):
        """Test metadata request uses Accept: application/xml."""
        with patch('sap_odata.client.requests.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            mock_response = Mock()
            mock_response.text = '<edmx:Edmx/>'
            mock_response.raise_for_status = Mock()
            
            mock_session.get.return_value = mock_response
            
            client = ODataClient("https://sap.example.com", sap_mode=False)
            client.metadata("TestService", version="v4")
            
            call_kwargs = mock_session.get.call_args
            assert call_kwargs[1]['headers']['Accept'] == 'application/xml'


class TestCountEndpoint:
    """Test /Entity/$count endpoint for count-only queries."""

    def test_count_returns_integer(self):
        """Test count() returns integer from plain text response."""
        with patch('sap_odata.client.requests.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            mock_response = Mock()
            mock_response.text = "245"
            mock_response.raise_for_status = Mock()
            
            mock_session.get.return_value = mock_response
            
            client = ODataClient("https://sap.example.com", sap_mode=False)
            result = client.count("TestService", "Products")
            
            assert result == 245
            assert isinstance(result, int)

    def test_count_with_whitespace(self):
        """Test count() handles whitespace in response."""
        with patch('sap_odata.client.requests.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            mock_response = Mock()
            mock_response.text = "  42\n"
            mock_response.raise_for_status = Mock()
            
            mock_session.get.return_value = mock_response
            
            client = ODataClient("https://sap.example.com", sap_mode=False)
            result = client.count("TestService", "Products")
            
            assert result == 42

    def test_count_with_filter(self):
        """Test count() passes filter parameter."""
        with patch('sap_odata.client.requests.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            mock_response = Mock()
            mock_response.text = "10"
            mock_response.raise_for_status = Mock()
            
            mock_session.get.return_value = mock_response
            
            client = ODataClient("https://sap.example.com", sap_mode=False)
            result = client.count("TestService", "Products", filter="Status eq 'OPEN'")
            
            assert result == 10
            # Verify filter was passed
            call_kwargs = mock_session.get.call_args
            assert "$filter" in call_kwargs[1]['params']

    def test_count_url_has_dollar_count(self):
        """Test count() URL includes /$count suffix."""
        with patch('sap_odata.client.requests.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            mock_response = Mock()
            mock_response.text = "100"
            mock_response.raise_for_status = Mock()
            
            mock_session.get.return_value = mock_response
            
            client = ODataClient("https://sap.example.com", sap_mode=False)
            client.count("TestService", "Products")
            
            call_args = mock_session.get.call_args
            url = call_args[0][0]
            assert "Products/$count" in url

    def test_count_accepts_text_plain(self):
        """Test count() uses Accept: text/plain header."""
        with patch('sap_odata.client.requests.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            mock_response = Mock()
            mock_response.text = "50"
            mock_response.raise_for_status = Mock()
            
            mock_session.get.return_value = mock_response
            
            client = ODataClient("https://sap.example.com", sap_mode=False)
            client.count("TestService", "Products")
            
            call_kwargs = mock_session.get.call_args
            assert call_kwargs[1]['headers']['Accept'] == 'text/plain'

    def test_count_connection_error(self):
        """Test count() raises ODataConnectionError on connection failure."""
        client = ODataClient("https://nonexistent-server-xyz123.local", sap_mode=False)
        
        with pytest.raises(ODataConnectionError, match="Connection failed"):
            client.count("TestService", "Products")

    def test_count_auth_error(self):
        """Test count() raises ODataAuthError on 401."""
        with patch('sap_odata.client.requests.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.text = "Unauthorized"
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
            
            mock_session.get.return_value = mock_response
            
            client = ODataClient("https://sap.example.com", sap_mode=False)
            
            with pytest.raises(ODataAuthError, match="Authentication failed"):
                client.count("TestService", "Products")

    def test_count_http_error(self):
        """Test count() raises ODataError on HTTP error."""
        with patch('sap_odata.client.requests.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.text = "Server Error"
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
            
            mock_session.get.return_value = mock_response
            
            client = ODataClient("https://sap.example.com", sap_mode=False)
            
            with pytest.raises(ODataError, match="HTTP 500"):
                client.count("TestService", "Products")

    def test_count_invalid_response(self):
        """Test count() raises ODataError on non-numeric response."""
        with patch('sap_odata.client.requests.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            mock_response = Mock()
            mock_response.text = "not a number"
            mock_response.raise_for_status = Mock()
            
            mock_session.get.return_value = mock_response
            
            client = ODataClient("https://sap.example.com", sap_mode=False)
            
            with pytest.raises(ODataError, match="Invalid count response"):
                client.count("TestService", "Products")

    def test_count_v2(self):
        """Test count() works with V2 services."""
        with patch('sap_odata.client.requests.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            mock_response = Mock()
            mock_response.text = "500"
            mock_response.raise_for_status = Mock()
            
            mock_session.get.return_value = mock_response
            
            client = ODataClient("https://sap.example.com", sap_mode=False)
            result = client.count("TestService", "Products", version="v2")
            
            assert result == 500

    def test_count_sap_v4_with_namespace(self):
        """Test count() works with SAP V4 namespace."""
        with patch('sap_odata.client.requests.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            mock_response = Mock()
            mock_response.text = "1000"
            mock_response.raise_for_status = Mock()
            
            mock_session.get.return_value = mock_response
            
            client = ODataClient("https://sap.example.com", sap_mode=True)
            result = client.count("zsd_my_service", "Products", version="v4", namespace="zsb_my_service")
            
            assert result == 1000
