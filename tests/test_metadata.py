"""
Tests for MetadataParser class.
"""

import pytest
from sap_odata.metadata import MetadataParser, EntityType, Property, NavigationProperty


class TestMetadataParserV4:
    """Test V4 metadata parsing."""
    
    def test_parse_v4_metadata(self, sample_metadata_v4):
        """Test parsing V4 metadata."""
        parser = MetadataParser(sample_metadata_v4)
        
        assert parser.odata_version == "v4"
        assert len(parser.entity_types) > 0
    
    def test_entity_types_parsed(self, sample_metadata_v4):
        """Test entity types are parsed correctly."""
        parser = MetadataParser(sample_metadata_v4)
        
        product = parser.get_entity_type("Product")
        assert product is not None
        assert product.name == "Product"
    
    def test_properties_parsed(self, sample_metadata_v4):
        """Test properties are parsed correctly."""
        parser = MetadataParser(sample_metadata_v4)
        
        product = parser.get_entity_type("Product")
        assert len(product.properties) > 0
        
        # Check ProductID property
        product_id = product.get_property("ProductID")
        assert product_id is not None
        assert product_id.type == "Edm.Int32"
        assert product_id.is_key is True
    
    def test_key_properties(self, sample_metadata_v4):
        """Test key properties are identified."""
        parser = MetadataParser(sample_metadata_v4)
        
        product = parser.get_entity_type("Product")
        assert "ProductID" in product.key_properties
        assert len(product.keys) == 1
    
    def test_navigation_properties(self, sample_metadata_v4):
        """Test navigation properties are parsed."""
        parser = MetadataParser(sample_metadata_v4)
        
        product = parser.get_entity_type("Product")
        category_nav = product.get_navigation("Category")
        assert category_nav is not None
        
        category = parser.get_entity_type("Category")
        products_nav = category.get_navigation("Products")
        assert products_nav is not None
        assert products_nav.is_collection is True
    
    def test_entity_sets_parsed(self, sample_metadata_v4):
        """Test entity sets are parsed."""
        parser = MetadataParser(sample_metadata_v4)
        
        assert len(parser.entity_sets) > 0
        
        products_set = parser.get_entity_set("Products")
        assert products_set is not None
        assert products_set.entity_type == "Product"


class TestMetadataParserV2:
    """Test V2 metadata parsing."""
    
    def test_parse_v2_metadata(self, sample_metadata_v2):
        """Test parsing V2 metadata."""
        parser = MetadataParser(sample_metadata_v2)
        
        assert parser.odata_version == "v2"
        assert len(parser.entity_types) > 0
    
    def test_v2_entity_types(self, sample_metadata_v2):
        """Test V2 entity types are parsed."""
        parser = MetadataParser(sample_metadata_v2)
        
        product = parser.get_entity_type("Product")
        assert product is not None
        assert len(product.properties) > 0


class TestProperty:
    """Test Property class."""
    
    def test_property_creation(self):
        """Test creating a property."""
        prop = Property(
            name="ProductID",
            type="Edm.Int32",
            nullable=False,
            is_key=True,
        )
        
        assert prop.name == "ProductID"
        assert prop.type == "Edm.Int32"
        assert prop.nullable is False
        assert prop.is_key is True
    
    def test_python_type_mapping(self):
        """Test EDM to Python type mapping."""
        test_cases = [
            ("Edm.String", "str"),
            ("Edm.Int32", "int"),
            ("Edm.Int64", "int"),
            ("Edm.Decimal", "float"),
            ("Edm.Boolean", "bool"),
            ("Edm.DateTime", "datetime"),
            ("Edm.Guid", "str"),
        ]
        
        for edm_type, python_type in test_cases:
            prop = Property(name="test", type=edm_type)
            assert prop.python_type == python_type
    
    def test_property_repr(self):
        """Test property string representation."""
        prop = Property(name="ID", type="Edm.Int32", is_key=True)
        repr_str = repr(prop)
        
        assert "ID" in repr_str
        assert "Edm.Int32" in repr_str
        assert "KEY" in repr_str


class TestNavigationProperty:
    """Test NavigationProperty class."""
    
    def test_navigation_creation(self):
        """Test creating a navigation property."""
        nav = NavigationProperty(
            name="Orders",
            target_entity="Order",
            is_collection=True,
        )
        
        assert nav.name == "Orders"
        assert nav.target_entity == "Order"
        assert nav.is_collection is True
    
    def test_navigation_repr(self):
        """Test navigation property string representation."""
        nav = NavigationProperty(
            name="Items",
            target_entity="OrderItem",
            is_collection=True,
        )
        
        repr_str = repr(nav)
        assert "Items" in repr_str
        assert "OrderItem" in repr_str


class TestEntityType:
    """Test EntityType class."""
    
    def test_entity_type_creation(self):
        """Test creating an entity type."""
        entity = EntityType(name="Product")
        entity.properties = [
            Property(name="ID", type="Edm.Int32", is_key=True),
            Property(name="Name", type="Edm.String"),
        ]
        entity.key_properties = ["ID"]
        
        assert entity.name == "Product"
        assert len(entity.properties) == 2
    
    def test_get_property(self):
        """Test getting property by name."""
        entity = EntityType(name="Product")
        entity.properties = [
            Property(name="ID", type="Edm.Int32"),
            Property(name="Name", type="Edm.String"),
        ]
        
        prop = entity.get_property("ID")
        assert prop is not None
        assert prop.type == "Edm.Int32"
        
        missing = entity.get_property("NonExistent")
        assert missing is None
    
    def test_keys_property(self):
        """Test keys property."""
        entity = EntityType(name="Product")
        entity.properties = [
            Property(name="ID", type="Edm.Int32", is_key=True),
            Property(name="Name", type="Edm.String", is_key=False),
        ]
        entity.key_properties = ["ID"]
        
        keys = entity.keys
        assert len(keys) == 1
        assert keys[0].name == "ID"


class TestMetadataToDict:
    """Test metadata to_dict functionality."""
    
    def test_to_dict(self, sample_metadata_v4):
        """Test converting metadata to dictionary."""
        parser = MetadataParser(sample_metadata_v4)
        d = parser.to_dict()
        
        assert "odata_version" in d
        assert "entity_types" in d
        assert "entity_sets" in d
        assert d["odata_version"] == "v4"


class TestInvalidMetadata:
    """Test handling of invalid metadata."""
    
    def test_invalid_xml(self):
        """Test handling invalid XML."""
        with pytest.raises(ValueError):
            MetadataParser("not valid xml")
    
    def test_empty_metadata(self):
        """Test handling empty metadata."""
        with pytest.raises(ValueError):
            MetadataParser("")
