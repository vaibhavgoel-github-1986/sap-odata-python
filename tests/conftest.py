"""
Pytest configuration and fixtures.
"""

import pytest


@pytest.fixture
def sample_v4_metadata():
    """Sample V4 metadata XML."""
    return """<?xml version="1.0" encoding="utf-8"?>
<edmx:Edmx Version="4.0" xmlns:edmx="http://docs.oasis-open.org/odata/ns/edmx">
  <edmx:DataServices>
    <Schema Namespace="TestService" xmlns="http://docs.oasis-open.org/odata/ns/edm">
      <EntityType Name="Customer">
        <Key>
          <PropertyRef Name="CustomerID"/>
        </Key>
        <Property Name="CustomerID" Type="Edm.String" Nullable="false"/>
        <Property Name="Name" Type="Edm.String"/>
      </EntityType>
      <EntityContainer Name="Container">
        <EntitySet Name="Customers" EntityType="TestService.Customer"/>
      </EntityContainer>
    </Schema>
  </edmx:DataServices>
</edmx:Edmx>
"""


@pytest.fixture
def sample_v2_response():
    """Sample V2 response data."""
    return {
        "d": {
            "results": [
                {"CustomerID": "C001", "Name": "Customer 1"},
                {"CustomerID": "C002", "Name": "Customer 2"},
            ],
            "__count": "100",
            "__next": "https://example.com/next"
        }
    }


@pytest.fixture
def sample_v4_response():
    """Sample V4 response data."""
    return {
        "value": [
            {"CustomerID": "C001", "Name": "Customer 1"},
            {"CustomerID": "C002", "Name": "Customer 2"},
        ],
        "@odata.count": 100,
        "@odata.nextLink": "https://example.com/next"
    }
