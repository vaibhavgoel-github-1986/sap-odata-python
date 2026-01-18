"""
Tests for OData Client.
"""

import pytest
import responses
from sap_odata import ODataClient, ODataConfig
from sap_odata.exceptions import ODataConnectionError, ODataAuthenticationError


class TestODataClientInit:
    """Tests for ODataClient initialization."""
    
    def test_init_with_valid_params(self):
        """Test client initialization with valid parameters."""
        client = ODataClient(
            host="https://sap.example.com",
            username="user",
            password="pass",
            client="100",
        )
        
        assert client.host == "https://sap.example.com"
        assert client.client == "100"
        assert not client.is_connected
    
    def test_init_strips_trailing_slash(self):
        """Test that trailing slash is removed from host."""
        client = ODataClient(
            host="https://sap.example.com/",
            username="user",
            password="pass",
        )
        
        assert client.host == "https://sap.example.com"
    
    def test_init_requires_host(self):
        """Test that host is required."""
        with pytest.raises(ValueError, match="host is required"):
            ODataClient(host="", username="user", password="pass")
    
    def test_init_requires_credentials(self):
        """Test that username and password are required."""
        with pytest.raises(ValueError, match="username and password are required"):
            ODataClient(host="https://sap.example.com", username="", password="pass")
        
        with pytest.raises(ValueError, match="username and password are required"):
            ODataClient(host="https://sap.example.com", username="user", password="")
    
    def test_init_with_custom_config(self):
        """Test client initialization with custom config."""
        config = ODataConfig(timeout=60, verify_ssl=False)
        
        client = ODataClient(
            host="https://sap.example.com",
            username="user",
            password="pass",
            config=config,
        )
        
        assert client.config.timeout == 60
        assert client.config.verify_ssl is False


class TestODataClientService:
    """Tests for ODataClient.service() method."""
    
    def test_service_v4(self):
        """Test creating a V4 service."""
        client = ODataClient(
            host="https://sap.example.com",
            username="user",
            password="pass",
        )
        
        service = client.service(
            name="ZSD_CUSTOMER_API",
            namespace="ZSB_CUSTOMER_API",
            version="v4",
        )
        
        assert service.name == "ZSD_CUSTOMER_API"
        assert service.namespace == "ZSB_CUSTOMER_API"
        assert service.version == "v4"
    
    def test_service_v2(self):
        """Test creating a V2 service."""
        client = ODataClient(
            host="https://sap.example.com",
            username="user",
            password="pass",
        )
        
        service = client.service(name="ZSALESORDER_SRV", version="v2")
        
        assert service.name == "ZSALESORDER_SRV"
        assert service.version == "v2"


class TestODataClientConnect:
    """Tests for ODataClient.connect() method."""
    
    @responses.activate
    def test_connect_success(self):
        """Test successful connection."""
        responses.add(
            responses.GET,
            "https://sap.example.com/sap/opu/odata/sap/",
            status=200,
        )
        
        client = ODataClient(
            host="https://sap.example.com",
            username="user",
            password="pass",
        )
        
        result = client.connect()
        
        assert result is client
        assert client.is_connected
    
    @responses.activate
    def test_connect_auth_failure(self):
        """Test connection with authentication failure."""
        responses.add(
            responses.GET,
            "https://sap.example.com/sap/opu/odata/sap/",
            status=401,
        )
        
        client = ODataClient(
            host="https://sap.example.com",
            username="user",
            password="wrong_pass",
        )
        
        with pytest.raises(ODataAuthenticationError):
            client.connect()


class TestODataClientContextManager:
    """Tests for ODataClient context manager."""
    
    @responses.activate
    def test_context_manager(self):
        """Test using client as context manager."""
        responses.add(
            responses.GET,
            "https://sap.example.com/sap/opu/odata/sap/",
            status=200,
        )
        
        with ODataClient(
            host="https://sap.example.com",
            username="user",
            password="pass",
        ) as client:
            assert client.is_connected
        
        assert not client.is_connected
