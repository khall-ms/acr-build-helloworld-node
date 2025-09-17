"""
Code Analyzer - Extract entities from C# and Go source files using tree-sitter.
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass

try:
    import tree_sitter
    from tree_sitter import Language, Parser
except ImportError:
    tree_sitter = None
    Language = None
    Parser = None

logger = logging.getLogger(__name__)


@dataclass
class CodeEntity:
    """Represents a code entity (class, interface, method, function, struct)."""
    name: str
    entity_type: str  # 'class', 'interface', 'method', 'function', 'struct', 'field'
    file_path: str
    start_line: int
    end_line: int
    start_column: int
    end_column: int
    parent: Optional[str] = None  # Parent entity name for nested entities
    modifiers: List[str] = None  # public, private, static, etc.
    parameters: List[str] = None  # For methods/functions
    return_type: Optional[str] = None  # For methods/functions

    def __post_init__(self):
        if self.modifiers is None:
            self.modifiers = []
        if self.parameters is None:
            self.parameters = []


class CodeAnalyzer:
    """Analyzes source code files and extracts entities using tree-sitter parsers."""
    
    def __init__(self):
        """Initialize the CodeAnalyzer."""
        self.parsers = {}
        self.languages = {}
        self._setup_parsers()
        
    def _setup_parsers(self):
        """Setup tree-sitter parsers for supported languages."""
        if tree_sitter is None:
            logger.warning("tree-sitter not available. Code analysis will be limited.")
            return
            
        try:
            # Note: In a real implementation, you would need to build the tree-sitter
            # language libraries. For this example, we'll handle the case where
            # they might not be available.
            self._setup_csharp_parser()
            self._setup_go_parser()
        except Exception as e:
            logger.warning(f"Failed to setup tree-sitter parsers: {e}")
    
    def _setup_csharp_parser(self):
        """Setup C# parser."""
        try:
            # This would normally load a compiled tree-sitter-csharp library
            # For demonstration, we'll create a mock implementation
            self.parsers['csharp'] = self._create_mock_parser('csharp')
            logger.info("C# parser initialized")
        except Exception as e:
            logger.warning(f"Failed to setup C# parser: {e}")
    
    def _setup_go_parser(self):
        """Setup Go parser."""
        try:
            # This would normally load a compiled tree-sitter-go library
            # For demonstration, we'll create a mock implementation
            self.parsers['go'] = self._create_mock_parser('go')
            logger.info("Go parser initialized")
        except Exception as e:
            logger.warning(f"Failed to setup Go parser: {e}")
    
    def _create_mock_parser(self, language: str):
        """Create a mock parser for demonstration purposes."""
        # In a real implementation, this would be:
        # Language.build_library('build/my-languages.so', [f'tree-sitter-{language}'])
        # language = Language('build/my-languages.so', language)
        # parser = Parser()
        # parser.set_language(language)
        # return parser
        return f"mock_{language}_parser"
    
    def analyze_file(self, file_path: Union[str, Path]) -> List[CodeEntity]:
        """
        Analyze a single source file and extract code entities.
        
        Args:
            file_path: Path to the source file
            
        Returns:
            List of CodeEntity objects found in the file
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return []
        
        file_extension = file_path.suffix.lower()
        language = self._get_language_from_extension(file_extension)
        
        if language is None:
            logger.warning(f"Unsupported file extension: {file_extension}")
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return self._parse_content(content, str(file_path), language)
        
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
            return []
    
    def analyze_directory(self, directory_path: Union[str, Path], recursive: bool = True) -> List[CodeEntity]:
        """
        Analyze all supported source files in a directory.
        
        Args:
            directory_path: Path to the directory
            recursive: Whether to search subdirectories
            
        Returns:
            List of CodeEntity objects found in all files
        """
        directory_path = Path(directory_path)
        
        if not directory_path.is_dir():
            logger.error(f"Directory not found: {directory_path}")
            return []
        
        entities = []
        pattern = "**/*" if recursive else "*"
        
        for file_path in directory_path.glob(pattern):
            if file_path.is_file() and self._is_supported_file(file_path):
                file_entities = self.analyze_file(file_path)
                entities.extend(file_entities)
        
        logger.info(f"Analyzed directory {directory_path}: found {len(entities)} entities")
        return entities
    
    def _get_language_from_extension(self, extension: str) -> Optional[str]:
        """Map file extension to language."""
        extension_map = {
            '.cs': 'csharp',
            '.go': 'go'
        }
        return extension_map.get(extension)
    
    def _is_supported_file(self, file_path: Path) -> bool:
        """Check if file has a supported extension."""
        return file_path.suffix.lower() in ['.cs', '.go']
    
    def _parse_content(self, content: str, file_path: str, language: str) -> List[CodeEntity]:
        """
        Parse file content and extract entities.
        
        This is a simplified implementation that demonstrates the structure.
        A real implementation would use tree-sitter to parse the AST.
        """
        entities = []
        
        if language == 'csharp':
            entities.extend(self._parse_csharp_content(content, file_path))
        elif language == 'go':
            entities.extend(self._parse_go_content(content, file_path))
        
        return entities
    
    def _parse_csharp_content(self, content: str, file_path: str) -> List[CodeEntity]:
        """Parse C# content using simple pattern matching (demo implementation)."""
        entities = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Simple pattern matching for demonstration
            if line.startswith('public class ') or line.startswith('class '):
                class_name = self._extract_name_from_declaration(line, 'class')
                if class_name:
                    entities.append(CodeEntity(
                        name=class_name,
                        entity_type='class',
                        file_path=file_path,
                        start_line=i + 1,
                        end_line=i + 1,  # Simplified - would need to find closing brace
                        start_column=1,
                        end_column=len(line),
                        modifiers=['public'] if 'public' in line else []
                    ))
            
            elif line.startswith('public interface ') or line.startswith('interface '):
                interface_name = self._extract_name_from_declaration(line, 'interface')
                if interface_name:
                    entities.append(CodeEntity(
                        name=interface_name,
                        entity_type='interface',
                        file_path=file_path,
                        start_line=i + 1,
                        end_line=i + 1,
                        start_column=1,
                        end_column=len(line),
                        modifiers=['public'] if 'public' in line else []
                    ))
            
            elif 'public ' in line and '(' in line and ')' in line:
                method_name = self._extract_method_name(line)
                if method_name:
                    entities.append(CodeEntity(
                        name=method_name,
                        entity_type='method',
                        file_path=file_path,
                        start_line=i + 1,
                        end_line=i + 1,
                        start_column=1,
                        end_column=len(line),
                        modifiers=['public'] if 'public' in line else []
                    ))
        
        return entities
    
    def _parse_go_content(self, content: str, file_path: str) -> List[CodeEntity]:
        """Parse Go content using simple pattern matching (demo implementation)."""
        entities = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Simple pattern matching for demonstration
            if line.startswith('type ') and ' struct' in line:
                struct_name = self._extract_go_struct_name(line)
                if struct_name:
                    entities.append(CodeEntity(
                        name=struct_name,
                        entity_type='struct',
                        file_path=file_path,
                        start_line=i + 1,
                        end_line=i + 1,
                        start_column=1,
                        end_column=len(line)
                    ))
            
            elif line.startswith('func '):
                func_name = self._extract_go_function_name(line)
                if func_name:
                    entities.append(CodeEntity(
                        name=func_name,
                        entity_type='function',
                        file_path=file_path,
                        start_line=i + 1,
                        end_line=i + 1,
                        start_column=1,
                        end_column=len(line)
                    ))
        
        return entities
    
    def _extract_name_from_declaration(self, line: str, keyword: str) -> Optional[str]:
        """Extract name from a class/interface declaration."""
        try:
            parts = line.split()
            keyword_index = -1
            for i, part in enumerate(parts):
                if keyword in part:
                    keyword_index = i
                    break
            
            if keyword_index >= 0 and keyword_index + 1 < len(parts):
                name = parts[keyword_index + 1]
                # Remove any generic type parameters or inheritance
                name = name.split('<')[0].split(':')[0].split('{')[0]
                return name.strip()
        except Exception:
            pass
        return None
    
    def _extract_method_name(self, line: str) -> Optional[str]:
        """Extract method name from a method declaration."""
        try:
            if '(' in line:
                before_paren = line[:line.index('(')]
                parts = before_paren.split()
                if len(parts) >= 2:
                    return parts[-1].strip()
        except Exception:
            pass
        return None
    
    def _extract_go_struct_name(self, line: str) -> Optional[str]:
        """Extract struct name from Go type declaration."""
        try:
            # Format: type StructName struct
            parts = line.split()
            if len(parts) >= 3 and parts[0] == 'type' and 'struct' in parts:
                return parts[1].strip()
        except Exception:
            pass
        return None
    
    def _extract_go_function_name(self, line: str) -> Optional[str]:
        """Extract function name from Go function declaration."""
        try:
            # Format: func FunctionName(...) or func (receiver) FunctionName(...)
            if '(' in line:
                before_paren = line[:line.index('(')]
                parts = before_paren.split()
                if len(parts) >= 2:
                    if ')' in parts[-1]:  # Method with receiver
                        # Look for the next part after receiver
                        full_line_parts = line.split()
                        for i, part in enumerate(full_line_parts):
                            if part.endswith(')') and i + 1 < len(full_line_parts):
                                next_part = full_line_parts[i + 1]
                                if '(' in next_part:
                                    return next_part[:next_part.index('(')].strip()
                                return next_part.strip()
                    else:
                        return parts[-1].strip()
        except Exception:
            pass
        return None

    def get_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions."""
        return ['.cs', '.go']
    
    def get_statistics(self, entities: List[CodeEntity]) -> Dict[str, Any]:
        """Get statistics about analyzed entities."""
        stats = {
            'total_entities': len(entities),
            'by_type': {},
            'by_file': {},
            'by_language': {}
        }
        
        for entity in entities:
            # Count by type
            entity_type = entity.entity_type
            stats['by_type'][entity_type] = stats['by_type'].get(entity_type, 0) + 1
            
            # Count by file
            file_path = entity.file_path
            stats['by_file'][file_path] = stats['by_file'].get(file_path, 0) + 1
            
            # Count by language (inferred from file extension)
            file_ext = Path(file_path).suffix.lower()
            language = self._get_language_from_extension(file_ext)
            if language:
                stats['by_language'][language] = stats['by_language'].get(language, 0) + 1
        
        return stats