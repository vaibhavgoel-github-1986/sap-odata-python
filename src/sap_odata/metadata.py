"""
SAP OData Metadata Parser.

Parses OData metadata XML and provides easy access to entity types,
properties, associations, and service structure.
"""

import xml.etree.ElementTree as ET
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field


# XML namespaces used in OData metadata
NAMESPACES = {
    "edmx": "http://docs.oasis-open.org/odata/ns/edmx",
    "edm": "http://docs.oasis-open.org/odata/ns/edm",
    # V2 namespaces
    "edmx2": "http://schemas.microsoft.com/ado/2007/06/edmx",
    "edm2": "http://schemas.microsoft.com/ado/2008/09/edm",
    "sap": "http://www.sap.com/Protocols/SAPData",
}


@dataclass
class Property:
    """
    Represents an entity property.
    
    Attributes:
        name: Property name (e.g., 'CustomerID', 'Name')
        type: EDM type (e.g., 'Edm.String', 'Edm.Int32')
        nullable: Whether the property can be null
        max_length: Maximum length for string properties
        is_key: Whether this is a key property
        label: Human-readable label (SAP annotation)
        description: Property description
    """
    name: str
    type: str
    nullable: bool = True
    max_length: Optional[int] = None
    is_key: bool = False
    label: Optional[str] = None
    description: Optional[str] = None
    
    @property
    def python_type(self) -> str:
        """Map EDM type to Python type hint."""
        type_map = {
            "Edm.String": "str",
            "Edm.Int32": "int",
            "Edm.Int64": "int",
            "Edm.Int16": "int",
            "Edm.Decimal": "float",
            "Edm.Double": "float",
            "Edm.Single": "float",
            "Edm.Boolean": "bool",
            "Edm.DateTime": "datetime",
            "Edm.DateTimeOffset": "datetime",
            "Edm.Date": "date",
            "Edm.Time": "time",
            "Edm.Guid": "str",
            "Edm.Binary": "bytes",
        }
        return type_map.get(self.type, "Any")
    
    def __repr__(self) -> str:
        key_marker = " [KEY]" if self.is_key else ""
        return f"Property({self.name}: {self.type}{key_marker})"


@dataclass
class NavigationProperty:
    """
    Represents a navigation property (relationship).
    
    Attributes:
        name: Navigation property name
        target_entity: Target entity type name
        is_collection: Whether it returns a collection
    """
    name: str
    target_entity: str
    is_collection: bool = False
    
    def __repr__(self) -> str:
        collection = "[]" if self.is_collection else ""
        return f"Navigation({self.name} -> {self.target_entity}{collection})"


@dataclass
class EntityType:
    """
    Represents an OData entity type.
    
    Attributes:
        name: Entity type name (e.g., 'Customer', 'SalesOrder')
        properties: List of Property objects
        navigation_properties: List of NavigationProperty objects
        key_properties: List of key property names
    """
    name: str
    properties: List[Property] = field(default_factory=list)
    navigation_properties: List[NavigationProperty] = field(default_factory=list)
    key_properties: List[str] = field(default_factory=list)
    
    @property
    def keys(self) -> List[Property]:
        """Get key properties."""
        return [p for p in self.properties if p.is_key]
    
    def get_property(self, name: str) -> Optional[Property]:
        """Get property by name."""
        for prop in self.properties:
            if prop.name == name:
                return prop
        return None
    
    def get_navigation(self, name: str) -> Optional[NavigationProperty]:
        """Get navigation property by name."""
        for nav in self.navigation_properties:
            if nav.name == name:
                return nav
        return None
    
    def __repr__(self) -> str:
        return (
            f"EntityType({self.name}, "
            f"properties={len(self.properties)}, "
            f"navigations={len(self.navigation_properties)})"
        )


@dataclass
class EntitySet:
    """
    Represents an OData entity set (collection endpoint).
    
    Attributes:
        name: Entity set name (URL path component)
        entity_type: Associated entity type name
    """
    name: str
    entity_type: str
    
    def __repr__(self) -> str:
        return f"EntitySet({self.name} -> {self.entity_type})"


class MetadataParser:
    """
    Parser for OData metadata XML.
    
    Automatically detects OData version (V2 vs V4) and parses
    the metadata to extract entity types, properties, and relationships.
    
    Example:
        >>> # Parse from XML string
        >>> parser = MetadataParser(xml_string)
        >>> 
        >>> # List all entity types
        >>> for entity in parser.entity_types:
        ...     print(f"{entity.name}: {[p.name for p in entity.properties]}")
        >>> 
        >>> # Get specific entity type
        >>> customer = parser.get_entity_type("Customer")
        >>> for prop in customer.properties:
        ...     print(f"  {prop.name}: {prop.type}")
        >>> 
        >>> # Get entity set
        >>> entity_set = parser.get_entity_set("Customers")
    """
    
    def __init__(self, xml_content: str):
        """
        Initialize parser with metadata XML.
        
        Args:
            xml_content: Raw metadata XML string
        """
        self.xml_content = xml_content
        self._entity_types: Dict[str, EntityType] = {}
        self._entity_sets: Dict[str, EntitySet] = {}
        self._odata_version: str = "v4"
        
        self._parse()
    
    @property
    def entity_types(self) -> List[EntityType]:
        """Get all entity types."""
        return list(self._entity_types.values())
    
    @property
    def entity_sets(self) -> List[EntitySet]:
        """Get all entity sets."""
        return list(self._entity_sets.values())
    
    @property
    def odata_version(self) -> str:
        """Detected OData version ('v2' or 'v4')."""
        return self._odata_version
    
    def get_entity_type(self, name: str) -> Optional[EntityType]:
        """
        Get entity type by name.
        
        Args:
            name: Entity type name
        
        Returns:
            EntityType or None if not found
        """
        return self._entity_types.get(name)
    
    def get_entity_set(self, name: str) -> Optional[EntitySet]:
        """
        Get entity set by name.
        
        Args:
            name: Entity set name
        
        Returns:
            EntitySet or None if not found
        """
        return self._entity_sets.get(name)
    
    def _parse(self) -> None:
        """Parse the metadata XML."""
        try:
            root = ET.fromstring(self.xml_content)
        except ET.ParseError as e:
            raise ValueError(f"Invalid metadata XML: {e}")
        
        # Detect OData version from namespace
        root_tag = root.tag
        if "schemas.microsoft.com" in root_tag:
            self._odata_version = "v2"
            self._parse_v2(root)
        else:
            self._odata_version = "v4"
            self._parse_v4(root)
    
    def _parse_v4(self, root: ET.Element) -> None:
        """Parse OData V4 metadata."""
        # Find Schema element
        for schema in root.findall(".//{http://docs.oasis-open.org/odata/ns/edm}Schema"):
            namespace = schema.get("Namespace", "")
            
            # Parse EntityTypes
            for et in schema.findall("{http://docs.oasis-open.org/odata/ns/edm}EntityType"):
                entity_type = self._parse_entity_type_v4(et, namespace)
                self._entity_types[entity_type.name] = entity_type
            
            # Parse EntityContainer for EntitySets
            container = schema.find("{http://docs.oasis-open.org/odata/ns/edm}EntityContainer")
            if container is not None:
                for es in container.findall("{http://docs.oasis-open.org/odata/ns/edm}EntitySet"):
                    name = es.get("Name", "")
                    entity_type = es.get("EntityType", "").split(".")[-1]
                    self._entity_sets[name] = EntitySet(name=name, entity_type=entity_type)
    
    def _parse_entity_type_v4(self, element: ET.Element, namespace: str) -> EntityType:
        """Parse V4 EntityType element."""
        name = element.get("Name", "")
        entity = EntityType(name=name)
        
        # Parse Key
        key_elem = element.find("{http://docs.oasis-open.org/odata/ns/edm}Key")
        if key_elem is not None:
            for prop_ref in key_elem.findall("{http://docs.oasis-open.org/odata/ns/edm}PropertyRef"):
                key_name = prop_ref.get("Name", "")
                entity.key_properties.append(key_name)
        
        # Parse Properties
        for prop in element.findall("{http://docs.oasis-open.org/odata/ns/edm}Property"):
            prop_name = prop.get("Name", "")
            prop_obj = Property(
                name=prop_name,
                type=prop.get("Type", "Edm.String"),
                nullable=prop.get("Nullable", "true").lower() == "true",
                max_length=int(prop.get("MaxLength")) if prop.get("MaxLength") else None,
                is_key=prop_name in entity.key_properties,
            )
            entity.properties.append(prop_obj)
        
        # Parse NavigationProperties
        for nav in element.findall("{http://docs.oasis-open.org/odata/ns/edm}NavigationProperty"):
            nav_type = nav.get("Type", "")
            is_collection = nav_type.startswith("Collection(")
            target = nav_type.replace("Collection(", "").replace(")", "").split(".")[-1]
            nav_obj = NavigationProperty(
                name=nav.get("Name", ""),
                target_entity=target,
                is_collection=is_collection,
            )
            entity.navigation_properties.append(nav_obj)
        
        return entity
    
    def _parse_v2(self, root: ET.Element) -> None:
        """Parse OData V2 metadata."""
        # V2 uses different namespaces
        edm_ns = "{http://schemas.microsoft.com/ado/2008/09/edm}"
        
        for schema in root.findall(f".//{edm_ns}Schema"):
            namespace = schema.get("Namespace", "")
            
            # Parse EntityTypes
            for et in schema.findall(f"{edm_ns}EntityType"):
                entity_type = self._parse_entity_type_v2(et, edm_ns, namespace)
                self._entity_types[entity_type.name] = entity_type
            
            # Parse EntityContainer
            container = schema.find(f"{edm_ns}EntityContainer")
            if container is not None:
                for es in container.findall(f"{edm_ns}EntitySet"):
                    name = es.get("Name", "")
                    entity_type = es.get("EntityType", "").split(".")[-1]
                    self._entity_sets[name] = EntitySet(name=name, entity_type=entity_type)
    
    def _parse_entity_type_v2(self, element: ET.Element, ns: str, namespace: str) -> EntityType:
        """Parse V2 EntityType element."""
        name = element.get("Name", "")
        entity = EntityType(name=name)
        
        # Parse Key
        key_elem = element.find(f"{ns}Key")
        if key_elem is not None:
            for prop_ref in key_elem.findall(f"{ns}PropertyRef"):
                key_name = prop_ref.get("Name", "")
                entity.key_properties.append(key_name)
        
        # Parse Properties
        sap_ns = "{http://www.sap.com/Protocols/SAPData}"
        for prop in element.findall(f"{ns}Property"):
            prop_name = prop.get("Name", "")
            prop_obj = Property(
                name=prop_name,
                type=prop.get("Type", "Edm.String"),
                nullable=prop.get("Nullable", "true").lower() == "true",
                max_length=int(prop.get("MaxLength")) if prop.get("MaxLength") else None,
                is_key=prop_name in entity.key_properties,
                label=prop.get(f"{sap_ns}label"),
            )
            entity.properties.append(prop_obj)
        
        # Parse NavigationProperties
        for nav in element.findall(f"{ns}NavigationProperty"):
            nav_obj = NavigationProperty(
                name=nav.get("Name", ""),
                target_entity=nav.get("ToRole", "").replace("Type", ""),
                is_collection=True,  # V2 associations are typically collections
            )
            entity.navigation_properties.append(nav_obj)
        
        return entity
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert parsed metadata to dictionary.
        
        Returns:
            Dictionary with entity types and sets
        """
        return {
            "odata_version": self._odata_version,
            "entity_types": {
                name: {
                    "name": et.name,
                    "key_properties": et.key_properties,
                    "properties": [
                        {
                            "name": p.name,
                            "type": p.type,
                            "nullable": p.nullable,
                            "is_key": p.is_key,
                        }
                        for p in et.properties
                    ],
                    "navigation_properties": [
                        {
                            "name": n.name,
                            "target": n.target_entity,
                            "is_collection": n.is_collection,
                        }
                        for n in et.navigation_properties
                    ],
                }
                for name, et in self._entity_types.items()
            },
            "entity_sets": {
                name: {"name": es.name, "entity_type": es.entity_type}
                for name, es in self._entity_sets.items()
            },
        }
    
    def __repr__(self) -> str:
        return (
            f"MetadataParser(version={self._odata_version}, "
            f"entity_types={len(self._entity_types)}, "
            f"entity_sets={len(self._entity_sets)})"
        )
