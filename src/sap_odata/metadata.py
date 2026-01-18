"""
Metadata - OData service metadata parsing and representation.
"""

from typing import List, Optional, Dict, Any, Literal
from dataclasses import dataclass, field
from lxml import etree


# OData EDMX namespaces
NAMESPACES = {
    "edmx": "http://docs.oasis-open.org/odata/ns/edmx",
    "edm": "http://docs.oasis-open.org/odata/ns/edm",
    "edmx2": "http://schemas.microsoft.com/ado/2007/06/edmx",
    "edm2": "http://schemas.microsoft.com/ado/2008/09/edm",
    "edm3": "http://schemas.microsoft.com/ado/2009/11/edm",
    "m": "http://schemas.microsoft.com/ado/2007/08/dataservices/metadata",
    "sap": "http://www.sap.com/Protocols/SAPData",
}


@dataclass
class Property:
    """
    Represents an entity type property.
    
    Attributes:
        name: Property name
        type: OData/EDM type (e.g., "Edm.String", "Edm.Int32")
        nullable: Whether the property can be null
        max_length: Maximum length for string properties
        precision: Precision for decimal properties
        scale: Scale for decimal properties
        is_key: Whether this is a key property
        label: Human-readable label (SAP annotation)
    """
    name: str
    type: str
    nullable: bool = True
    max_length: Optional[int] = None
    precision: Optional[int] = None
    scale: Optional[int] = None
    is_key: bool = False
    label: Optional[str] = None
    
    @property
    def python_type(self) -> type:
        """Get equivalent Python type."""
        type_map = {
            "Edm.String": str,
            "Edm.Int16": int,
            "Edm.Int32": int,
            "Edm.Int64": int,
            "Edm.Decimal": float,
            "Edm.Double": float,
            "Edm.Single": float,
            "Edm.Boolean": bool,
            "Edm.DateTime": str,
            "Edm.DateTimeOffset": str,
            "Edm.Date": str,
            "Edm.Time": str,
            "Edm.Binary": bytes,
            "Edm.Guid": str,
        }
        return type_map.get(self.type, str)


@dataclass
class NavigationProperty:
    """
    Represents a navigation property (relationship).
    
    Attributes:
        name: Navigation property name
        type: Target entity type
        partner: Partner navigation property name
        is_collection: Whether it returns a collection
    """
    name: str
    type: str
    partner: Optional[str] = None
    is_collection: bool = False


@dataclass
class EntityType:
    """
    Represents an OData entity type.
    
    Attributes:
        name: Entity type name
        properties: List of properties
        navigation_properties: List of navigation properties
        key_properties: Names of key properties
    """
    name: str
    properties: List[Property] = field(default_factory=list)
    navigation_properties: List[NavigationProperty] = field(default_factory=list)
    key_properties: List[str] = field(default_factory=list)
    
    def property(self, name: str) -> Optional[Property]:
        """Get a property by name."""
        for prop in self.properties:
            if prop.name == name:
                return prop
        return None
    
    def navigation(self, name: str) -> Optional[NavigationProperty]:
        """Get a navigation property by name."""
        for nav in self.navigation_properties:
            if nav.name == name:
                return nav
        return None


@dataclass
class EntitySet:
    """
    Represents an OData entity set.
    
    Attributes:
        name: Entity set name
        entity_type: Associated entity type
        entity_type_name: Name of the entity type
    """
    name: str
    entity_type: Optional[EntityType] = None
    entity_type_name: str = ""


@dataclass
class FunctionImport:
    """
    Represents a function import (V2) or action/function (V4).
    
    Attributes:
        name: Function name
        return_type: Return type
        http_method: HTTP method (GET, POST)
        parameters: List of parameter definitions
    """
    name: str
    return_type: Optional[str] = None
    http_method: str = "GET"
    parameters: List[Dict[str, Any]] = field(default_factory=list)


class Metadata:
    """
    OData service metadata container.
    
    Parses and provides access to entity types, entity sets,
    and other metadata information.
    
    Example:
        >>> metadata = service.metadata()
        >>> for entity_set in metadata.entity_sets:
        ...     print(f"{entity_set.name}: {len(entity_set.entity_type.properties)} properties")
    """
    
    def __init__(self) -> None:
        """Initialize empty metadata."""
        self._entity_types: Dict[str, EntityType] = {}
        self._entity_sets: Dict[str, EntitySet] = {}
        self._function_imports: Dict[str, FunctionImport] = {}
        self._version: str = "v4"
        self._raw_xml: str = ""
    
    @property
    def entity_types(self) -> List[EntityType]:
        """Get all entity types."""
        return list(self._entity_types.values())
    
    @property
    def entity_sets(self) -> List[EntitySet]:
        """Get all entity sets."""
        return list(self._entity_sets.values())
    
    @property
    def function_imports(self) -> List[FunctionImport]:
        """Get all function imports."""
        return list(self._function_imports.values())
    
    def entity_type(self, name: str) -> Optional[EntityType]:
        """Get entity type by name."""
        return self._entity_types.get(name)
    
    def entity_set(self, name: str) -> Optional[EntitySet]:
        """Get entity set by name."""
        return self._entity_sets.get(name)
    
    def has_entity(self, name: str) -> bool:
        """Check if entity set exists."""
        return name in self._entity_sets
    
    @classmethod
    def from_xml(cls, xml_content: str, version: Literal["v2", "v4"] = "v4") -> "Metadata":
        """
        Parse metadata from XML content.
        
        Args:
            xml_content: Raw XML metadata string
            version: OData version
        
        Returns:
            Parsed Metadata object
        """
        metadata = cls()
        metadata._raw_xml = xml_content
        metadata._version = version
        
        try:
            root = etree.fromstring(xml_content.encode("utf-8"))
        except etree.XMLSyntaxError as e:
            raise ValueError(f"Invalid metadata XML: {e}")
        
        # Determine namespace based on version
        if version == "v4":
            metadata._parse_v4(root)
        else:
            metadata._parse_v2(root)
        
        return metadata
    
    def _parse_v4(self, root: etree._Element) -> None:
        """Parse OData V4 metadata."""
        # Find Schema element
        for schema in root.iter("{http://docs.oasis-open.org/odata/ns/edm}Schema"):
            namespace = schema.get("Namespace", "")
            
            # Parse EntityTypes
            for entity_elem in schema.findall(
                "{http://docs.oasis-open.org/odata/ns/edm}EntityType"
            ):
                entity_type = self._parse_entity_type_v4(entity_elem)
                self._entity_types[entity_type.name] = entity_type
            
            # Parse EntityContainer
            for container in schema.findall(
                "{http://docs.oasis-open.org/odata/ns/edm}EntityContainer"
            ):
                # Parse EntitySets
                for entity_set_elem in container.findall(
                    "{http://docs.oasis-open.org/odata/ns/edm}EntitySet"
                ):
                    name = entity_set_elem.get("Name", "")
                    entity_type_name = entity_set_elem.get("EntityType", "")
                    # Remove namespace prefix if present
                    if "." in entity_type_name:
                        entity_type_name = entity_type_name.split(".")[-1]
                    
                    entity_set = EntitySet(
                        name=name,
                        entity_type_name=entity_type_name,
                        entity_type=self._entity_types.get(entity_type_name),
                    )
                    self._entity_sets[name] = entity_set
    
    def _parse_v2(self, root: etree._Element) -> None:
        """Parse OData V2 metadata."""
        # Find Schema element (try different namespaces)
        schema = None
        for ns in ["edm2", "edm3"]:
            schemas = root.findall(f".//{{{NAMESPACES[ns]}}}Schema")
            if schemas:
                schema = schemas[0]
                edm_ns = NAMESPACES[ns]
                break
        
        if schema is None:
            return
        
        # Parse EntityTypes
        for entity_elem in schema.findall(f"{{{edm_ns}}}EntityType"):
            entity_type = self._parse_entity_type_v2(entity_elem, edm_ns)
            self._entity_types[entity_type.name] = entity_type
        
        # Parse EntityContainer
        for container in schema.findall(f"{{{edm_ns}}}EntityContainer"):
            # Parse EntitySets
            for entity_set_elem in container.findall(f"{{{edm_ns}}}EntitySet"):
                name = entity_set_elem.get("Name", "")
                entity_type_name = entity_set_elem.get("EntityType", "")
                # Remove namespace prefix if present
                if "." in entity_type_name:
                    entity_type_name = entity_type_name.split(".")[-1]
                
                entity_set = EntitySet(
                    name=name,
                    entity_type_name=entity_type_name,
                    entity_type=self._entity_types.get(entity_type_name),
                )
                self._entity_sets[name] = entity_set
    
    def _parse_entity_type_v4(self, elem: etree._Element) -> EntityType:
        """Parse a V4 EntityType element."""
        name = elem.get("Name", "")
        entity_type = EntityType(name=name)
        
        # Parse Key properties
        key_elem = elem.find("{http://docs.oasis-open.org/odata/ns/edm}Key")
        if key_elem is not None:
            for prop_ref in key_elem.findall(
                "{http://docs.oasis-open.org/odata/ns/edm}PropertyRef"
            ):
                entity_type.key_properties.append(prop_ref.get("Name", ""))
        
        # Parse Properties
        for prop_elem in elem.findall("{http://docs.oasis-open.org/odata/ns/edm}Property"):
            prop = Property(
                name=prop_elem.get("Name", ""),
                type=prop_elem.get("Type", "Edm.String"),
                nullable=prop_elem.get("Nullable", "true").lower() == "true",
                max_length=int(prop_elem.get("MaxLength")) if prop_elem.get("MaxLength") else None,
                is_key=prop_elem.get("Name", "") in entity_type.key_properties,
            )
            entity_type.properties.append(prop)
        
        # Parse NavigationProperties
        for nav_elem in elem.findall(
            "{http://docs.oasis-open.org/odata/ns/edm}NavigationProperty"
        ):
            nav_type = nav_elem.get("Type", "")
            is_collection = nav_type.startswith("Collection(")
            if is_collection:
                nav_type = nav_type[11:-1]  # Remove "Collection(" and ")"
            
            nav = NavigationProperty(
                name=nav_elem.get("Name", ""),
                type=nav_type,
                partner=nav_elem.get("Partner"),
                is_collection=is_collection,
            )
            entity_type.navigation_properties.append(nav)
        
        return entity_type
    
    def _parse_entity_type_v2(self, elem: etree._Element, edm_ns: str) -> EntityType:
        """Parse a V2 EntityType element."""
        name = elem.get("Name", "")
        entity_type = EntityType(name=name)
        
        # Parse Key properties
        key_elem = elem.find(f"{{{edm_ns}}}Key")
        if key_elem is not None:
            for prop_ref in key_elem.findall(f"{{{edm_ns}}}PropertyRef"):
                entity_type.key_properties.append(prop_ref.get("Name", ""))
        
        # Parse Properties
        for prop_elem in elem.findall(f"{{{edm_ns}}}Property"):
            prop = Property(
                name=prop_elem.get("Name", ""),
                type=prop_elem.get("Type", "Edm.String"),
                nullable=prop_elem.get("Nullable", "true").lower() == "true",
                max_length=int(prop_elem.get("MaxLength")) if prop_elem.get("MaxLength") else None,
                is_key=prop_elem.get("Name", "") in entity_type.key_properties,
                label=prop_elem.get(f"{{{NAMESPACES['sap']}}}label"),
            )
            entity_type.properties.append(prop)
        
        # Parse NavigationProperties
        for nav_elem in elem.findall(f"{{{edm_ns}}}NavigationProperty"):
            nav = NavigationProperty(
                name=nav_elem.get("Name", ""),
                type=nav_elem.get("ToRole", ""),
            )
            entity_type.navigation_properties.append(nav)
        
        return entity_type
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"Metadata(entity_sets={len(self._entity_sets)}, "
            f"entity_types={len(self._entity_types)})"
        )
