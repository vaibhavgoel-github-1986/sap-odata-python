"""
Tests for Metadata parsing.
"""

import pytest
from sap_odata.metadata import Metadata, EntityType, EntitySet, Property


SAMPLE_V4_METADATA = """<?xml version="1.0" encoding="utf-8"?>
<edmx:Edmx Version="4.0" xmlns:edmx="http://docs.oasis-open.org/odata/ns/edmx">
  <edmx:DataServices>
    <Schema Namespace="TestService" xmlns="http://docs.oasis-open.org/odata/ns/edm">
      <EntityType Name="Customer">
        <Key>
          <PropertyRef Name="CustomerID"/>
        </Key>
        <Property Name="CustomerID" Type="Edm.String" Nullable="false" MaxLength="10"/>
        <Property Name="Name" Type="Edm.String" MaxLength="100"/>
        <Property Name="Country" Type="Edm.String" MaxLength="3"/>
        <Property Name="Active" Type="Edm.Boolean"/>
        <NavigationProperty Name="Orders" Type="Collection(TestService.Order)"/>
      </EntityType>
      <EntityType Name="Order">
        <Key>
          <PropertyRef Name="OrderID"/>
        </Key>
        <Property Name="OrderID" Type="Edm.Int32" Nullable="false"/>
        <Property Name="Total" Type="Edm.Decimal" Precision="15" Scale="2"/>
      </EntityType>
      <EntityContainer Name="Container">
        <EntitySet Name="Customers" EntityType="TestService.Customer"/>
        <EntitySet Name="Orders" EntityType="TestService.Order"/>
      </EntityContainer>
    </Schema>
  </edmx:DataServices>
</edmx:Edmx>
"""


class TestMetadataParsing:
    """Tests for metadata XML parsing."""
    
    def test_parse_v4_metadata(self):
        """Test parsing V4 metadata."""
        metadata = Metadata.from_xml(SAMPLE_V4_METADATA, version="v4")
        
        assert len(metadata.entity_types) == 2
        assert len(metadata.entity_sets) == 2
    
    def test_entity_type_properties(self):
        """Test entity type properties are parsed correctly."""
        metadata = Metadata.from_xml(SAMPLE_V4_METADATA, version="v4")
        
        customer_type = metadata.entity_type("Customer")
        assert customer_type is not None
        assert customer_type.name == "Customer"
        assert len(customer_type.properties) == 4
        assert customer_type.key_properties == ["CustomerID"]
    
    def test_property_attributes(self):
        """Test property attributes are parsed correctly."""
        metadata = Metadata.from_xml(SAMPLE_V4_METADATA, version="v4")
        
        customer_type = metadata.entity_type("Customer")
        customer_id_prop = customer_type.property("CustomerID")
        
        assert customer_id_prop is not None
        assert customer_id_prop.name == "CustomerID"
        assert customer_id_prop.type == "Edm.String"
        assert customer_id_prop.nullable is False
        assert customer_id_prop.max_length == 10
        assert customer_id_prop.is_key is True
    
    def test_navigation_properties(self):
        """Test navigation properties are parsed correctly."""
        metadata = Metadata.from_xml(SAMPLE_V4_METADATA, version="v4")
        
        customer_type = metadata.entity_type("Customer")
        assert len(customer_type.navigation_properties) == 1
        
        orders_nav = customer_type.navigation("Orders")
        assert orders_nav is not None
        assert orders_nav.name == "Orders"
        assert orders_nav.is_collection is True
    
    def test_entity_sets(self):
        """Test entity sets are parsed correctly."""
        metadata = Metadata.from_xml(SAMPLE_V4_METADATA, version="v4")
        
        customers_set = metadata.entity_set("Customers")
        assert customers_set is not None
        assert customers_set.name == "Customers"
        assert customers_set.entity_type_name == "Customer"
        assert customers_set.entity_type is not None
    
    def test_has_entity(self):
        """Test has_entity method."""
        metadata = Metadata.from_xml(SAMPLE_V4_METADATA, version="v4")
        
        assert metadata.has_entity("Customers") is True
        assert metadata.has_entity("Products") is False
    
    def test_invalid_xml(self):
        """Test parsing invalid XML."""
        with pytest.raises(ValueError, match="Invalid metadata XML"):
            Metadata.from_xml("<invalid>xml", version="v4")


class TestProperty:
    """Tests for Property class."""
    
    def test_python_type_mapping(self):
        """Test Python type mapping."""
        assert Property(name="test", type="Edm.String").python_type == str
        assert Property(name="test", type="Edm.Int32").python_type == int
        assert Property(name="test", type="Edm.Boolean").python_type == bool
        assert Property(name="test", type="Edm.Decimal").python_type == float
        assert Property(name="test", type="Unknown").python_type == str  # Default
