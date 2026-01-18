"""
Pytest configuration and fixtures for SAP OData Python tests.
"""

import pytest
from sap_odata import SAPODataClient


# Public Northwind OData service URLs
NORTHWIND_V4_HOST = "https://services.odata.org"
NORTHWIND_V4_SERVICE = "V4/Northwind/Northwind.svc"

NORTHWIND_V2_HOST = "https://services.odata.org"
NORTHWIND_V2_SERVICE = "V2/Northwind/Northwind.svc"


@pytest.fixture
def v4_client():
    """Create a client for Northwind V4 service."""
    return SAPODataClient(
        host=NORTHWIND_V4_HOST,
        username="",
        password="",
        is_sap=False,
    )


@pytest.fixture
def v2_client():
    """Create a client for Northwind V2 service."""
    return SAPODataClient(
        host=NORTHWIND_V2_HOST,
        username="",
        password="",
        is_sap=False,
    )


@pytest.fixture
def sample_metadata_v4():
    """Sample V4 metadata XML for testing."""
    return '''<?xml version="1.0" encoding="utf-8"?>
<edmx:Edmx Version="4.0" xmlns:edmx="http://docs.oasis-open.org/odata/ns/edmx">
  <edmx:DataServices>
    <Schema Namespace="NorthwindModel" xmlns="http://docs.oasis-open.org/odata/ns/edm">
      <EntityType Name="Product">
        <Key>
          <PropertyRef Name="ProductID"/>
        </Key>
        <Property Name="ProductID" Type="Edm.Int32" Nullable="false"/>
        <Property Name="ProductName" Type="Edm.String"/>
        <Property Name="UnitPrice" Type="Edm.Decimal"/>
        <Property Name="UnitsInStock" Type="Edm.Int16"/>
        <Property Name="Discontinued" Type="Edm.Boolean"/>
        <NavigationProperty Name="Category" Type="NorthwindModel.Category"/>
      </EntityType>
      <EntityType Name="Category">
        <Key>
          <PropertyRef Name="CategoryID"/>
        </Key>
        <Property Name="CategoryID" Type="Edm.Int32" Nullable="false"/>
        <Property Name="CategoryName" Type="Edm.String"/>
        <Property Name="Description" Type="Edm.String"/>
        <NavigationProperty Name="Products" Type="Collection(NorthwindModel.Product)"/>
      </EntityType>
      <EntityContainer Name="NorthwindEntities">
        <EntitySet Name="Products" EntityType="NorthwindModel.Product"/>
        <EntitySet Name="Categories" EntityType="NorthwindModel.Category"/>
      </EntityContainer>
    </Schema>
  </edmx:DataServices>
</edmx:Edmx>'''


@pytest.fixture
def sample_metadata_v2():
    """Sample V2 metadata XML for testing."""
    return '''<?xml version="1.0" encoding="utf-8"?>
<edmx:Edmx Version="1.0" xmlns:edmx="http://schemas.microsoft.com/ado/2007/06/edmx">
  <edmx:DataServices m:DataServiceVersion="2.0" xmlns:m="http://schemas.microsoft.com/ado/2007/08/dataservices/metadata">
    <Schema Namespace="NorthwindModel" xmlns="http://schemas.microsoft.com/ado/2008/09/edm">
      <EntityType Name="Product">
        <Key>
          <PropertyRef Name="ProductID"/>
        </Key>
        <Property Name="ProductID" Type="Edm.Int32" Nullable="false"/>
        <Property Name="ProductName" Type="Edm.String"/>
        <Property Name="UnitPrice" Type="Edm.Decimal"/>
      </EntityType>
      <EntityContainer Name="NorthwindEntities">
        <EntitySet Name="Products" EntityType="NorthwindModel.Product"/>
      </EntityContainer>
    </Schema>
  </edmx:DataServices>
</edmx:Edmx>'''
