"""
ACR Diagrams - Code Analysis and Knowledge Graph Generation

This package provides tools for analyzing source code and generating knowledge graphs.
"""

__version__ = "1.0.0"
__author__ = "ACR Diagrams Team"

from .code_analyzer import CodeAnalyzer
from .knowledge_graph import KnowledgeGraphGenerator
from .turtle_exporter import TurtleExporter

__all__ = [
    "CodeAnalyzer",
    "KnowledgeGraphGenerator", 
    "TurtleExporter"
]