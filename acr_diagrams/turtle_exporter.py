"""
Turtle Exporter - Export knowledge graphs to various RDF formats.
"""

import logging
from pathlib import Path
from typing import Union, Optional, Dict, Any

try:
    from rdflib import Graph
    from rdflib.plugins.serializers.turtle import TurtleSerializer
except ImportError:
    Graph = None
    TurtleSerializer = None

logger = logging.getLogger(__name__)


class TurtleExporter:
    """Exports RDF graphs to multiple formats with validation and pretty-printing."""
    
    SUPPORTED_FORMATS = {
        'turtle': 'turtle',
        'ttl': 'turtle',
        'n3': 'n3',
        'nt': 'nt',
        'xml': 'xml',
        'rdf': 'xml',
        'json-ld': 'json-ld',
        'jsonld': 'json-ld'
    }
    
    def __init__(self):
        """Initialize the TurtleExporter."""
        if Graph is None:
            raise ImportError("rdflib is required for RDF export")
    
    def export_to_file(self, graph: 'Graph', output_path: Union[str, Path], 
                      format_type: str = 'turtle', pretty_print: bool = True) -> bool:
        """
        Export RDF graph to a file.
        
        Args:
            graph: RDF graph to export
            output_path: Path to output file
            format_type: Output format ('turtle', 'n3', 'xml', 'json-ld')
            pretty_print: Whether to format output for readability
            
        Returns:
            True if export successful, False otherwise
        """
        output_path = Path(output_path)
        
        if not self._validate_format(format_type):
            logger.error(f"Unsupported format: {format_type}")
            return False
        
        try:
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Get the rdflib format string
            rdflib_format = self.SUPPORTED_FORMATS[format_type.lower()]
            
            # Serialize the graph
            serialized_data = self._serialize_graph(graph, rdflib_format, pretty_print)
            
            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(serialized_data)
            
            logger.info(f"Successfully exported graph to {output_path} in {format_type} format")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export graph to {output_path}: {e}")
            return False
    
    def export_to_string(self, graph: 'Graph', format_type: str = 'turtle', 
                        pretty_print: bool = True) -> Optional[str]:
        """
        Export RDF graph to a string.
        
        Args:
            graph: RDF graph to export
            format_type: Output format ('turtle', 'n3', 'xml', 'json-ld')
            pretty_print: Whether to format output for readability
            
        Returns:
            Serialized graph as string, or None if export failed
        """
        if not self._validate_format(format_type):
            logger.error(f"Unsupported format: {format_type}")
            return None
        
        try:
            rdflib_format = self.SUPPORTED_FORMATS[format_type.lower()]
            return self._serialize_graph(graph, rdflib_format, pretty_print)
            
        except Exception as e:
            logger.error(f"Failed to export graph to string: {e}")
            return None
    
    def _serialize_graph(self, graph: 'Graph', rdflib_format: str, pretty_print: bool) -> str:
        """
        Serialize the RDF graph to a string.
        
        Args:
            graph: RDF graph to serialize
            rdflib_format: RDFLib format string
            pretty_print: Whether to format for readability
            
        Returns:
            Serialized graph as string
        """
        if pretty_print and rdflib_format == 'turtle':
            # Use custom turtle formatting for better readability
            return self._serialize_turtle_pretty(graph)
        else:
            # Use standard rdflib serialization
            return graph.serialize(format=rdflib_format)
    
    def _serialize_turtle_pretty(self, graph: 'Graph') -> str:
        """
        Serialize to Turtle format with pretty formatting.
        
        Args:
            graph: RDF graph to serialize
            
        Returns:
            Pretty-formatted Turtle string
        """
        # Get standard turtle serialization
        turtle_data = graph.serialize(format='turtle')
        
        # Apply additional formatting for readability
        lines = turtle_data.split('\n')
        formatted_lines = []
        
        in_prefix_section = True
        current_subject = None
        
        for line in lines:
            line = line.strip()
            
            if not line:
                formatted_lines.append('')
                continue
            
            # Handle prefix declarations
            if line.startswith('@prefix'):
                if not in_prefix_section:
                    formatted_lines.append('')  # Add space before prefix section
                    in_prefix_section = True
                formatted_lines.append(line)
                continue
            
            # Handle subject declarations
            if line and not line.startswith(' ') and not line.startswith('\t') and ':' in line and not line.startswith('@'):
                if in_prefix_section:
                    formatted_lines.append('')  # Add space after prefix section
                    in_prefix_section = False
                
                if current_subject is not None:
                    formatted_lines.append('')  # Add space between subjects
                
                current_subject = line.split()[0] if line.split() else None
                formatted_lines.append(line)
                continue
            
            # Handle predicate-object pairs
            if line.startswith(' ') or line.startswith('\t'):
                formatted_lines.append(line)
                continue
            
            # Handle other lines
            formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def _validate_format(self, format_type: str) -> bool:
        """
        Validate that the format is supported.
        
        Args:
            format_type: Format to validate
            
        Returns:
            True if format is supported, False otherwise
        """
        return format_type.lower() in self.SUPPORTED_FORMATS
    
    def validate_output(self, output_path: Union[str, Path], format_type: str = 'turtle') -> bool:
        """
        Validate that an exported file is valid RDF.
        
        Args:
            output_path: Path to the file to validate
            format_type: Expected format of the file
            
        Returns:
            True if file is valid RDF, False otherwise
        """
        output_path = Path(output_path)
        
        if not output_path.exists():
            logger.error(f"File does not exist: {output_path}")
            return False
        
        try:
            # Try to parse the file back into a graph
            test_graph = Graph()
            rdflib_format = self.SUPPORTED_FORMATS.get(format_type.lower(), format_type)
            test_graph.parse(str(output_path), format=rdflib_format)
            
            logger.info(f"File {output_path} is valid {format_type} format with {len(test_graph)} triples")
            return True
            
        except Exception as e:
            logger.error(f"File {output_path} is not valid {format_type} format: {e}")
            return False
    
    def get_format_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about supported formats.
        
        Returns:
            Dictionary with format information
        """
        format_info = {
            'turtle': {
                'name': 'Turtle',
                'description': 'Terse RDF Triple Language',
                'mime_type': 'text/turtle',
                'file_extension': '.ttl',
                'human_readable': True,
                'compact': True
            },
            'n3': {
                'name': 'Notation3',
                'description': 'Notation3 (N3) format',
                'mime_type': 'text/n3',
                'file_extension': '.n3',
                'human_readable': True,
                'compact': True
            },
            'nt': {
                'name': 'N-Triples',
                'description': 'N-Triples format',
                'mime_type': 'application/n-triples',
                'file_extension': '.nt',
                'human_readable': True,
                'compact': False
            },
            'xml': {
                'name': 'RDF/XML',
                'description': 'RDF/XML format',
                'mime_type': 'application/rdf+xml',
                'file_extension': '.rdf',
                'human_readable': False,
                'compact': False
            },
            'json-ld': {
                'name': 'JSON-LD',
                'description': 'JSON-LD format',
                'mime_type': 'application/ld+json',
                'file_extension': '.jsonld',
                'human_readable': True,
                'compact': True
            }
        }
        
        return format_info
    
    def export_multiple_formats(self, graph: 'Graph', base_path: Union[str, Path], 
                               formats: list = None) -> Dict[str, bool]:
        """
        Export the same graph to multiple formats.
        
        Args:
            graph: RDF graph to export
            base_path: Base path for output files (without extension)
            formats: List of formats to export (if None, exports all supported formats)
            
        Returns:
            Dictionary mapping format to success status
        """
        if formats is None:
            formats = list(self.get_format_info().keys())
        
        base_path = Path(base_path)
        results = {}
        
        for format_type in formats:
            if not self._validate_format(format_type):
                logger.warning(f"Skipping unsupported format: {format_type}")
                results[format_type] = False
                continue
            
            # Determine file extension
            format_info = self.get_format_info().get(format_type, {})
            extension = format_info.get('file_extension', f'.{format_type}')
            
            output_path = base_path.with_suffix(extension)
            success = self.export_to_file(graph, output_path, format_type)
            results[format_type] = success
            
            if success:
                logger.info(f"Exported {format_type} format to {output_path}")
            else:
                logger.error(f"Failed to export {format_type} format")
        
        return results
    
    def get_export_statistics(self, graph: 'Graph') -> Dict[str, Any]:
        """
        Get statistics about what will be exported.
        
        Args:
            graph: RDF graph to analyze
            
        Returns:
            Dictionary with export statistics
        """
        stats = {
            'total_triples': len(graph),
            'namespaces': dict(graph.namespaces()),
            'subjects': len(set(graph.subjects())),
            'predicates': len(set(graph.predicates())),
            'objects': len(set(graph.objects()))
        }
        
        # Estimate file sizes for different formats
        sample_turtle = graph.serialize(format='turtle')
        stats['estimated_sizes'] = {
            'turtle': len(sample_turtle),
            'n3': int(len(sample_turtle) * 1.1),  # N3 is usually slightly larger
            'nt': int(len(sample_turtle) * 1.5),  # N-Triples has less compression
            'xml': int(len(sample_turtle) * 2.0),  # XML is more verbose
            'json-ld': int(len(sample_turtle) * 1.3)  # JSON-LD is moderately verbose
        }
        
        return stats
    
    def create_manifest(self, export_results: Dict[str, bool], base_path: Union[str, Path]) -> bool:
        """
        Create a manifest file describing the exported files.
        
        Args:
            export_results: Results from export_multiple_formats
            base_path: Base path used for exports
            
        Returns:
            True if manifest created successfully, False otherwise
        """
        try:
            base_path = Path(base_path)
            manifest_path = base_path.with_suffix('.manifest.json')
            
            import json
            from datetime import datetime
            
            manifest = {
                'created': datetime.now().isoformat(),
                'base_name': base_path.name,
                'exports': {}
            }
            
            format_info = self.get_format_info()
            
            for format_type, success in export_results.items():
                if success and format_type in format_info:
                    info = format_info[format_type]
                    extension = info.get('file_extension', f'.{format_type}')
                    file_path = base_path.with_suffix(extension)
                    
                    manifest['exports'][format_type] = {
                        'file_name': file_path.name,
                        'format_name': info.get('name', format_type),
                        'mime_type': info.get('mime_type', 'unknown'),
                        'description': info.get('description', ''),
                        'file_size': file_path.stat().st_size if file_path.exists() else 0
                    }
            
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2)
            
            logger.info(f"Created manifest file: {manifest_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create manifest: {e}")
            return False
    
    def get_supported_formats(self) -> list:
        """Get list of supported export formats."""
        return list(self.SUPPORTED_FORMATS.keys())