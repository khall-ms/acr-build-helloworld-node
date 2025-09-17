"""
Knowledge Graph Generator - Creates RDF graphs with custom ontology using rdflib.
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

try:
    from rdflib import Graph, Namespace, URIRef, Literal, BNode
    from rdflib.namespace import RDF, RDFS, OWL, XSD
except ImportError:
    Graph = None
    Namespace = None
    URIRef = None
    Literal = None
    BNode = None
    RDF = None
    RDFS = None
    OWL = None
    XSD = None

from .code_analyzer import CodeEntity

logger = logging.getLogger(__name__)


class KnowledgeGraphGenerator:
    """Generates RDF knowledge graphs from code entities."""
    
    def __init__(self, base_uri: str = "http://example.org/acr-diagrams/"):
        """
        Initialize the knowledge graph generator.
        
        Args:
            base_uri: Base URI for the ontology
        """
        if Graph is None:
            raise ImportError("rdflib is required for knowledge graph generation")
        
        self.base_uri = base_uri
        self.graph = Graph()
        self.namespace = Namespace(base_uri)
        
        # Define custom ontology namespaces
        self.CODE = Namespace(f"{base_uri}code/")
        self.ONTOLOGY = Namespace(f"{base_uri}ontology/")
        
        # Bind namespaces
        self.graph.bind("code", self.CODE)
        self.graph.bind("onto", self.ONTOLOGY)
        self.graph.bind("rdfs", RDFS)
        self.graph.bind("owl", OWL)
        
        self._create_ontology()
    
    def _create_ontology(self):
        """Create the custom ontology for code entities."""
        logger.info("Creating code analysis ontology")
        
        # Define classes
        self._define_class("CodeEntity", "Base class for all code entities")
        self._define_class("Class", "A class definition", parent="CodeEntity")
        self._define_class("Interface", "An interface definition", parent="CodeEntity")  
        self._define_class("Method", "A method definition", parent="CodeEntity")
        self._define_class("Function", "A function definition", parent="CodeEntity")
        self._define_class("Struct", "A struct definition", parent="CodeEntity")
        self._define_class("Field", "A field definition", parent="CodeEntity")
        self._define_class("SourceFile", "A source code file")
        
        # Define properties
        self._define_property("hasName", "rdfs:Literal", "The name of the entity")
        self._define_property("hasType", "rdfs:Literal", "The type of the entity")
        self._define_property("hasFilePath", "rdfs:Literal", "File path where entity is defined")
        self._define_property("hasStartLine", "xsd:integer", "Starting line number")
        self._define_property("hasEndLine", "xsd:integer", "Ending line number")
        self._define_property("hasStartColumn", "xsd:integer", "Starting column number")
        self._define_property("hasEndColumn", "xsd:integer", "Ending column number")
        self._define_property("hasModifier", "rdfs:Literal", "Access modifier (public, private, etc.)")
        self._define_property("hasParameter", "rdfs:Literal", "Method/function parameter")
        self._define_property("hasReturnType", "rdfs:Literal", "Method/function return type")
        self._define_property("belongsToFile", "SourceFile", "File that contains this entity")
        self._define_property("hasParent", "CodeEntity", "Parent entity (for nested entities)")
        self._define_property("contains", "CodeEntity", "Contains child entity")
        self._define_property("hasLanguage", "rdfs:Literal", "Programming language")
    
    def _define_class(self, class_name: str, description: str, parent: str = None):
        """Define an OWL class in the ontology."""
        class_uri = self.ONTOLOGY[class_name]
        self.graph.add((class_uri, RDF.type, OWL.Class))
        self.graph.add((class_uri, RDFS.label, Literal(class_name)))
        self.graph.add((class_uri, RDFS.comment, Literal(description)))
        
        if parent:
            parent_uri = self.ONTOLOGY[parent]
            self.graph.add((class_uri, RDFS.subClassOf, parent_uri))
    
    def _define_property(self, prop_name: str, range_type: str, description: str):
        """Define an OWL property in the ontology."""
        prop_uri = self.ONTOLOGY[prop_name]
        self.graph.add((prop_uri, RDF.type, OWL.DatatypeProperty))
        self.graph.add((prop_uri, RDFS.label, Literal(prop_name)))
        self.graph.add((prop_uri, RDFS.comment, Literal(description)))
        
        # Set range based on type
        if range_type == "rdfs:Literal":
            self.graph.add((prop_uri, RDFS.range, RDFS.Literal))
        elif range_type == "xsd:integer":
            self.graph.add((prop_uri, RDFS.range, XSD.integer))
        elif range_type.startswith("xsd:"):
            range_uri = XSD[range_type[4:]]
            self.graph.add((prop_uri, RDFS.range, range_uri))
        else:
            # Assume it's a class reference
            range_uri = self.ONTOLOGY[range_type]
            self.graph.add((prop_uri, RDFS.range, range_uri))
            self.graph.add((prop_uri, RDF.type, OWL.ObjectProperty))
    
    def add_entities(self, entities: List[CodeEntity]) -> int:
        """
        Add code entities to the knowledge graph.
        
        Args:
            entities: List of CodeEntity objects to add
            
        Returns:
            Number of entities successfully added
        """
        added_count = 0
        file_uris = {}  # Cache file URIs
        
        logger.info(f"Adding {len(entities)} entities to knowledge graph")
        
        for entity in entities:
            try:
                # Create entity URI
                entity_uri = self._create_entity_uri(entity)
                
                # Add basic entity information
                self._add_entity_basic_info(entity_uri, entity)
                
                # Add file relationship
                file_uri = self._get_or_create_file_uri(entity.file_path, file_uris)
                self.graph.add((entity_uri, self.ONTOLOGY.belongsToFile, file_uri))
                
                # Add parent relationship if exists
                if entity.parent:
                    parent_uri = self._find_parent_entity_uri(entity.parent, entity.file_path)
                    if parent_uri:
                        self.graph.add((entity_uri, self.ONTOLOGY.hasParent, parent_uri))
                        self.graph.add((parent_uri, self.ONTOLOGY.contains, entity_uri))
                
                added_count += 1
                
            except Exception as e:
                logger.error(f"Failed to add entity {entity.name}: {e}")
        
        logger.info(f"Successfully added {added_count} entities to knowledge graph")
        return added_count
    
    def _create_entity_uri(self, entity: CodeEntity) -> URIRef:
        """Create a unique URI for a code entity."""
        # Create a unique identifier based on file path, name, and line number
        file_name = Path(entity.file_path).stem
        safe_name = entity.name.replace(" ", "_").replace("<", "_").replace(">", "_")
        entity_id = f"{file_name}_{safe_name}_{entity.start_line}"
        return self.CODE[entity_id]
    
    def _add_entity_basic_info(self, entity_uri: URIRef, entity: CodeEntity):
        """Add basic information about an entity to the graph."""
        # Determine entity class
        entity_class = self._get_entity_class(entity.entity_type)
        self.graph.add((entity_uri, RDF.type, entity_class))
        
        # Add basic properties
        self.graph.add((entity_uri, self.ONTOLOGY.hasName, Literal(entity.name)))
        self.graph.add((entity_uri, self.ONTOLOGY.hasType, Literal(entity.entity_type)))
        self.graph.add((entity_uri, self.ONTOLOGY.hasFilePath, Literal(entity.file_path)))
        self.graph.add((entity_uri, self.ONTOLOGY.hasStartLine, Literal(entity.start_line)))
        self.graph.add((entity_uri, self.ONTOLOGY.hasEndLine, Literal(entity.end_line)))
        self.graph.add((entity_uri, self.ONTOLOGY.hasStartColumn, Literal(entity.start_column)))
        self.graph.add((entity_uri, self.ONTOLOGY.hasEndColumn, Literal(entity.end_column)))
        
        # Add modifiers
        for modifier in entity.modifiers:
            self.graph.add((entity_uri, self.ONTOLOGY.hasModifier, Literal(modifier)))
        
        # Add parameters for methods/functions
        for parameter in entity.parameters:
            self.graph.add((entity_uri, self.ONTOLOGY.hasParameter, Literal(parameter)))
        
        # Add return type if exists
        if entity.return_type:
            self.graph.add((entity_uri, self.ONTOLOGY.hasReturnType, Literal(entity.return_type)))
        
        # Add language based on file extension
        language = self._get_language_from_file_path(entity.file_path)
        if language:
            self.graph.add((entity_uri, self.ONTOLOGY.hasLanguage, Literal(language)))
    
    def _get_entity_class(self, entity_type: str) -> URIRef:
        """Get the OWL class URI for an entity type."""
        type_mapping = {
            'class': 'Class',
            'interface': 'Interface',
            'method': 'Method',
            'function': 'Function',
            'struct': 'Struct',
            'field': 'Field'
        }
        class_name = type_mapping.get(entity_type.lower(), 'CodeEntity')
        return self.ONTOLOGY[class_name]
    
    def _get_or_create_file_uri(self, file_path: str, file_cache: Dict[str, URIRef]) -> URIRef:
        """Get or create a URI for a source file."""
        if file_path in file_cache:
            return file_cache[file_path]
        
        # Create file URI
        file_name = Path(file_path).name.replace(".", "_")
        file_uri = self.CODE[f"file_{file_name}"]
        
        # Add file information
        self.graph.add((file_uri, RDF.type, self.ONTOLOGY.SourceFile))
        self.graph.add((file_uri, self.ONTOLOGY.hasFilePath, Literal(file_path)))
        self.graph.add((file_uri, self.ONTOLOGY.hasName, Literal(Path(file_path).name)))
        
        # Add language
        language = self._get_language_from_file_path(file_path)
        if language:
            self.graph.add((file_uri, self.ONTOLOGY.hasLanguage, Literal(language)))
        
        file_cache[file_path] = file_uri
        return file_uri
    
    def _get_language_from_file_path(self, file_path: str) -> Optional[str]:
        """Determine programming language from file extension."""
        extension = Path(file_path).suffix.lower()
        language_map = {
            '.cs': 'C#',
            '.go': 'Go'
        }
        return language_map.get(extension)
    
    def _find_parent_entity_uri(self, parent_name: str, file_path: str) -> Optional[URIRef]:
        """Find the URI of a parent entity by name and file."""
        # This is a simplified implementation
        # In practice, you might need a more sophisticated lookup mechanism
        file_name = Path(file_path).stem
        safe_name = parent_name.replace(" ", "_").replace("<", "_").replace(">", "_")
        # We don't know the line number, so this is approximate
        potential_uri = self.CODE[f"{file_name}_{safe_name}_0"]
        
        # Check if this entity exists in the graph
        if (potential_uri, None, None) in self.graph:
            return potential_uri
        
        return None
    
    def query(self, sparql_query: str) -> Any:
        """
        Execute a SPARQL query against the knowledge graph.
        
        Args:
            sparql_query: SPARQL query string
            
        Returns:
            Query results
        """
        try:
            return self.graph.query(sparql_query)
        except Exception as e:
            logger.error(f"SPARQL query failed: {e}")
            return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the knowledge graph."""
        stats = {
            'total_triples': len(self.graph),
            'entity_counts': {},
            'file_counts': 0,
            'language_counts': {}
        }
        
        # Count entities by type
        entity_types = ['Class', 'Interface', 'Method', 'Function', 'Struct', 'Field']
        for entity_type in entity_types:
            entity_class_uri = self.ONTOLOGY[entity_type]
            count = len(list(self.graph.subjects(RDF.type, entity_class_uri)))
            if count > 0:
                stats['entity_counts'][entity_type] = count
        
        # Count files
        file_class_uri = self.ONTOLOGY.SourceFile
        stats['file_counts'] = len(list(self.graph.subjects(RDF.type, file_class_uri)))
        
        # Count by language
        for s, p, o in self.graph.triples((None, self.ONTOLOGY.hasLanguage, None)):
            language = str(o)
            stats['language_counts'][language] = stats['language_counts'].get(language, 0) + 1
        
        return stats
    
    def find_entities_by_type(self, entity_type: str) -> List[Dict[str, Any]]:
        """
        Find all entities of a specific type.
        
        Args:
            entity_type: Type of entity to find (Class, Interface, Method, etc.)
            
        Returns:
            List of entity information dictionaries
        """
        entity_class_uri = self.ONTOLOGY[entity_type]
        entities = []
        
        for entity_uri in self.graph.subjects(RDF.type, entity_class_uri):
            entity_info = self._get_entity_info(entity_uri)
            entities.append(entity_info)
        
        return entities
    
    def find_entities_in_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Find all entities in a specific file.
        
        Args:
            file_path: Path to the source file
            
        Returns:
            List of entity information dictionaries
        """
        entities = []
        
        for entity_uri in self.graph.subjects(self.ONTOLOGY.hasFilePath, Literal(file_path)):
            entity_info = self._get_entity_info(entity_uri)
            entities.append(entity_info)
        
        return entities
    
    def _get_entity_info(self, entity_uri: URIRef) -> Dict[str, Any]:
        """Extract entity information from the graph."""
        info = {'uri': str(entity_uri)}
        
        # Get basic properties
        for prop_name, prop_uri in [
            ('name', self.ONTOLOGY.hasName),
            ('type', self.ONTOLOGY.hasType),
            ('file_path', self.ONTOLOGY.hasFilePath),
            ('start_line', self.ONTOLOGY.hasStartLine),
            ('end_line', self.ONTOLOGY.hasEndLine),
            ('language', self.ONTOLOGY.hasLanguage)
        ]:
            value = self.graph.value(entity_uri, prop_uri)
            if value:
                info[prop_name] = str(value)
        
        # Get modifiers
        modifiers = []
        for modifier in self.graph.objects(entity_uri, self.ONTOLOGY.hasModifier):
            modifiers.append(str(modifier))
        if modifiers:
            info['modifiers'] = modifiers
        
        # Get parameters
        parameters = []
        for param in self.graph.objects(entity_uri, self.ONTOLOGY.hasParameter):
            parameters.append(str(param))
        if parameters:
            info['parameters'] = parameters
        
        return info
    
    def get_graph(self) -> 'Graph':
        """Get the underlying RDF graph."""
        return self.graph
    
    def clear(self):
        """Clear all data from the knowledge graph."""
        # Keep the ontology, remove only the instance data
        new_graph = Graph()
        new_graph.bind("code", self.CODE)
        new_graph.bind("onto", self.ONTOLOGY)
        new_graph.bind("rdfs", RDFS)
        new_graph.bind("owl", OWL)
        
        # Copy ontology triples (classes and properties)
        for s, p, o in self.graph:
            if (isinstance(s, URIRef) and str(s).startswith(str(self.ONTOLOGY)) and
                p in [RDF.type, RDFS.label, RDFS.comment, RDFS.subClassOf, RDFS.range]):
                new_graph.add((s, p, o))
        
        self.graph = new_graph
        self._create_ontology()
        
        logger.info("Knowledge graph cleared")