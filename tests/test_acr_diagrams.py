"""
Basic tests for ACR Diagrams components.
"""

import unittest
import tempfile
from pathlib import Path

from acr_diagrams.code_analyzer import CodeAnalyzer, CodeEntity
from acr_diagrams.knowledge_graph import KnowledgeGraphGenerator
from acr_diagrams.turtle_exporter import TurtleExporter


class TestCodeAnalyzer(unittest.TestCase):
    """Test the CodeAnalyzer class."""
    
    def setUp(self):
        self.analyzer = CodeAnalyzer()
    
    def test_supported_extensions(self):
        """Test that analyzer supports expected file extensions."""
        extensions = self.analyzer.get_supported_extensions()
        self.assertIn('.cs', extensions)
        self.assertIn('.go', extensions)
    
    def test_analyze_csharp_content(self):
        """Test C# content analysis."""
        csharp_content = '''
        public class TestClass
        {
            public void TestMethod()
            {
            }
            
            public interface ITestInterface
            {
            }
        }
        '''
        
        entities = self.analyzer._parse_csharp_content(csharp_content, "test.cs")
        
        # Should find class and method
        entity_types = [e.entity_type for e in entities]
        entity_names = [e.name for e in entities]
        
        self.assertIn('class', entity_types)
        self.assertIn('TestClass', entity_names)
    
    def test_analyze_go_content(self):
        """Test Go content analysis."""
        go_content = '''
        type TestStruct struct {
            Name string
        }
        
        func TestFunction() {
        }
        
        func (t *TestStruct) TestMethod() {
        }
        '''
        
        entities = self.analyzer._parse_go_content(go_content, "test.go")
        
        # Should find struct and functions
        entity_types = [e.entity_type for e in entities]
        entity_names = [e.name for e in entities]
        
        self.assertIn('struct', entity_types)
        self.assertIn('function', entity_types)
        self.assertIn('TestStruct', entity_names)
        self.assertIn('TestFunction', entity_names)
    
    def test_statistics(self):
        """Test statistics generation."""
        entities = [
            CodeEntity("TestClass", "class", "test.cs", 1, 10, 1, 20),
            CodeEntity("TestMethod", "method", "test.cs", 5, 8, 5, 15),
            CodeEntity("TestStruct", "struct", "test.go", 1, 5, 1, 10)
        ]
        
        stats = self.analyzer.get_statistics(entities)
        
        self.assertEqual(stats['total_entities'], 3)
        self.assertEqual(stats['by_type']['class'], 1)
        self.assertEqual(stats['by_type']['method'], 1)
        self.assertEqual(stats['by_type']['struct'], 1)


class TestKnowledgeGraphGenerator(unittest.TestCase):
    """Test the KnowledgeGraphGenerator class."""
    
    def setUp(self):
        try:
            self.kg_generator = KnowledgeGraphGenerator()
        except ImportError:
            self.skipTest("rdflib not available")
    
    def test_add_entities(self):
        """Test adding entities to knowledge graph."""
        entities = [
            CodeEntity("TestClass", "class", "test.cs", 1, 10, 1, 20),
            CodeEntity("TestMethod", "method", "test.cs", 5, 8, 5, 15)
        ]
        
        added_count = self.kg_generator.add_entities(entities)
        self.assertEqual(added_count, 2)
        
        # Check statistics
        stats = self.kg_generator.get_statistics()
        self.assertGreater(stats['total_triples'], 0)
        self.assertIn('Class', stats['entity_counts'])
        self.assertIn('Method', stats['entity_counts'])
    
    def test_find_entities_by_type(self):
        """Test finding entities by type."""
        entities = [
            CodeEntity("TestClass", "class", "test.cs", 1, 10, 1, 20),
            CodeEntity("TestMethod", "method", "test.cs", 5, 8, 5, 15)
        ]
        
        self.kg_generator.add_entities(entities)
        
        classes = self.kg_generator.find_entities_by_type('Class')
        methods = self.kg_generator.find_entities_by_type('Method')
        
        self.assertEqual(len(classes), 1)
        self.assertEqual(len(methods), 1)
        self.assertEqual(classes[0]['name'], 'TestClass')
        self.assertEqual(methods[0]['name'], 'TestMethod')


class TestTurtleExporter(unittest.TestCase):
    """Test the TurtleExporter class."""
    
    def setUp(self):
        try:
            self.exporter = TurtleExporter()
            self.kg_generator = KnowledgeGraphGenerator()
        except ImportError:
            self.skipTest("rdflib not available")
    
    def test_supported_formats(self):
        """Test that exporter supports expected formats."""
        formats = self.exporter.get_supported_formats()
        self.assertIn('turtle', formats)
        self.assertIn('n3', formats)
        self.assertIn('xml', formats)
        self.assertIn('json-ld', formats)
    
    def test_export_to_string(self):
        """Test exporting graph to string."""
        # Create a simple graph
        entities = [CodeEntity("TestClass", "class", "test.cs", 1, 10, 1, 20)]
        self.kg_generator.add_entities(entities)
        graph = self.kg_generator.get_graph()
        
        # Export to string
        turtle_output = self.exporter.export_to_string(graph, 'turtle')
        self.assertIsNotNone(turtle_output)
        self.assertIn('@prefix', turtle_output)
    
    def test_export_to_file(self):
        """Test exporting graph to file."""
        # Create a simple graph
        entities = [CodeEntity("TestClass", "class", "test.cs", 1, 10, 1, 20)]
        self.kg_generator.add_entities(entities)
        graph = self.kg_generator.get_graph()
        
        # Export to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ttl', delete=False) as temp_file:
            temp_path = Path(temp_file.name)
        
        try:
            success = self.exporter.export_to_file(graph, temp_path, 'turtle')
            self.assertTrue(success)
            self.assertTrue(temp_path.exists())
            
            # Validate the output
            is_valid = self.exporter.validate_output(temp_path, 'turtle')
            self.assertTrue(is_valid)
        finally:
            if temp_path.exists():
                temp_path.unlink()
    
    def test_format_info(self):
        """Test format information retrieval."""
        format_info = self.exporter.get_format_info()
        
        self.assertIn('turtle', format_info)
        self.assertIn('name', format_info['turtle'])
        self.assertIn('mime_type', format_info['turtle'])
        self.assertIn('file_extension', format_info['turtle'])


if __name__ == '__main__':
    unittest.main()