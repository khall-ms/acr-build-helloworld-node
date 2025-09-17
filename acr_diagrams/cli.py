"""
CLI Interface - Command-line interface for ACR Diagrams code analysis and knowledge graph generation.
"""

import sys
import logging
from pathlib import Path
from typing import Optional, List

try:
    import click
except ImportError:
    click = None

from .code_analyzer import CodeAnalyzer
from .knowledge_graph import KnowledgeGraphGenerator  
from .turtle_exporter import TurtleExporter


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )


def print_statistics(stats: dict, title: str = "Statistics"):
    """Print formatted statistics."""
    click.echo(f"\n{title}:")
    click.echo("-" * len(title))
    
    for key, value in stats.items():
        if isinstance(value, dict):
            click.echo(f"{key}:")
            for subkey, subvalue in value.items():
                click.echo(f"  {subkey}: {subvalue}")
        else:
            click.echo(f"{key}: {value}")


def print_entities(entities: List, limit: int = 10):
    """Print entity information in a formatted way."""
    if not entities:
        click.echo("No entities found.")
        return
    
    click.echo(f"\nFound {len(entities)} entities:")
    click.echo("-" * 40)
    
    for i, entity in enumerate(entities[:limit]):
        if hasattr(entity, 'name'):  # CodeEntity object
            click.echo(f"{i+1}. {entity.entity_type}: {entity.name}")
            click.echo(f"   File: {entity.file_path}:{entity.start_line}")
            if entity.modifiers:
                click.echo(f"   Modifiers: {', '.join(entity.modifiers)}")
        else:  # Dictionary from knowledge graph
            click.echo(f"{i+1}. {entity.get('type', 'Unknown')}: {entity.get('name', 'Unknown')}")
            click.echo(f"   File: {entity.get('file_path', 'Unknown')}:{entity.get('start_line', 'Unknown')}")
            if 'modifiers' in entity:
                click.echo(f"   Modifiers: {', '.join(entity['modifiers'])}")
        click.echo()
    
    if len(entities) > limit:
        click.echo(f"... and {len(entities) - limit} more entities.")


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx, verbose):
    """ACR Diagrams - Code Analysis and Knowledge Graph Generation Tool."""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    setup_logging(verbose)


@cli.command()
@click.argument('source_path', type=click.Path(exists=True))
@click.option('--recursive', '-r', is_flag=True, default=True, 
              help='Recursively analyze subdirectories')
@click.option('--output', '-o', type=click.Path(), 
              help='Output file path for analysis results')
@click.option('--format', '-f', type=click.Choice(['turtle', 'n3', 'xml', 'json-ld']), 
              default='turtle', help='Output format')
@click.option('--statistics', '-s', is_flag=True, 
              help='Show analysis statistics')
@click.option('--list-entities', '-l', is_flag=True, 
              help='List found entities')
@click.option('--limit', type=int, default=10, 
              help='Limit number of entities to display')
@click.pass_context
def analyze(ctx, source_path, recursive, output, format, statistics, list_entities, limit):
    """Analyze source code and generate knowledge graph."""
    
    click.echo(f"Analyzing source code in: {source_path}")
    
    try:
        # Initialize components
        analyzer = CodeAnalyzer()
        kg_generator = KnowledgeGraphGenerator()
        exporter = TurtleExporter()
        
        # Analyze source code
        source_path = Path(source_path)
        if source_path.is_file():
            entities = analyzer.analyze_file(source_path)
        else:
            entities = analyzer.analyze_directory(source_path, recursive=recursive)
        
        if not entities:
            click.echo("No code entities found.")
            return
        
        click.echo(f"Found {len(entities)} code entities")
        
        # Generate knowledge graph
        click.echo("Generating knowledge graph...")
        added_count = kg_generator.add_entities(entities)
        click.echo(f"Added {added_count} entities to knowledge graph")
        
        # Show statistics if requested
        if statistics:
            analyzer_stats = analyzer.get_statistics(entities)
            kg_stats = kg_generator.get_statistics()
            
            print_statistics(analyzer_stats, "Code Analysis Statistics")
            print_statistics(kg_stats, "Knowledge Graph Statistics")
        
        # List entities if requested
        if list_entities:
            print_entities(entities, limit)
        
        # Export if output path specified
        if output:
            click.echo(f"Exporting knowledge graph to {output} in {format} format...")
            graph = kg_generator.get_graph()
            success = exporter.export_to_file(graph, output, format)
            
            if success:
                click.echo(f"Successfully exported to {output}")
                
                # Validate the output
                if exporter.validate_output(output, format):
                    click.echo("Output validation passed")
                else:
                    click.echo("Warning: Output validation failed")
            else:
                click.echo("Export failed", err=True)
                sys.exit(1)
        
    except Exception as e:
        click.echo(f"Error during analysis: {e}", err=True)
        if ctx.obj.get('verbose'):
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.argument('input_path', type=click.Path(exists=True))
@click.argument('output_base', type=click.Path())
@click.option('--formats', '-f', multiple=True, 
              type=click.Choice(['turtle', 'n3', 'xml', 'json-ld']),
              help='Export formats (can be specified multiple times)')
@click.option('--all-formats', is_flag=True, 
              help='Export to all supported formats')
@click.option('--validate', is_flag=True, 
              help='Validate exported files')
@click.option('--manifest', is_flag=True, 
              help='Create export manifest file')
@click.pass_context
def export(ctx, input_path, output_base, formats, all_formats, validate, manifest):
    """Export existing knowledge graph to various formats."""
    
    try:
        # Load existing graph
        kg_generator = KnowledgeGraphGenerator()
        graph = kg_generator.get_graph()
        
        # Try to load from input file
        try:
            graph.parse(str(input_path), format='turtle')
            click.echo(f"Loaded knowledge graph from {input_path}")
        except Exception as e:
            click.echo(f"Failed to load graph from {input_path}: {e}", err=True)
            sys.exit(1)
        
        exporter = TurtleExporter()
        
        # Determine formats to export
        if all_formats:
            export_formats = exporter.get_supported_formats()
        elif formats:
            export_formats = list(formats)
        else:
            export_formats = ['turtle']  # Default
        
        click.echo(f"Exporting to formats: {', '.join(export_formats)}")
        
        # Export to multiple formats
        results = exporter.export_multiple_formats(graph, output_base, export_formats)
        
        # Report results
        successful_exports = []
        failed_exports = []
        
        for format_type, success in results.items():
            if success:
                successful_exports.append(format_type)
            else:
                failed_exports.append(format_type)
        
        if successful_exports:
            click.echo(f"Successfully exported: {', '.join(successful_exports)}")
        
        if failed_exports:
            click.echo(f"Failed to export: {', '.join(failed_exports)}", err=True)
        
        # Validate exports if requested
        if validate and successful_exports:
            click.echo("Validating exported files...")
            format_info = exporter.get_format_info()
            
            for format_type in successful_exports:
                info = format_info.get(format_type, {})
                extension = info.get('file_extension', f'.{format_type}')
                output_path = Path(output_base).with_suffix(extension)
                
                if exporter.validate_output(output_path, format_type):
                    click.echo(f"✓ {format_type} format validation passed")
                else:
                    click.echo(f"✗ {format_type} format validation failed")
        
        # Create manifest if requested
        if manifest:
            if exporter.create_manifest(results, output_base):
                click.echo("Export manifest created")
            else:
                click.echo("Failed to create manifest", err=True)
        
        # Show export statistics
        export_stats = exporter.get_export_statistics(graph)
        print_statistics(export_stats, "Export Statistics")
        
    except Exception as e:
        click.echo(f"Error during export: {e}", err=True)
        if ctx.obj.get('verbose'):
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.argument('graph_path', type=click.Path(exists=True))
@click.argument('query_file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), 
              help='Output file for query results')
@click.option('--format', '-f', type=click.Choice(['table', 'json', 'csv']), 
              default='table', help='Output format for results')
@click.pass_context
def query(ctx, graph_path, query_file, output, format):
    """Execute SPARQL query against knowledge graph."""
    
    try:
        # Load knowledge graph
        kg_generator = KnowledgeGraphGenerator()
        graph = kg_generator.get_graph()
        graph.parse(str(graph_path), format='turtle')
        
        click.echo(f"Loaded knowledge graph from {graph_path}")
        
        # Read query
        with open(query_file, 'r', encoding='utf-8') as f:
            sparql_query = f.read()
        
        click.echo(f"Executing query from {query_file}")
        
        # Execute query
        results = kg_generator.query(sparql_query)
        
        if results is None:
            click.echo("Query execution failed", err=True)
            sys.exit(1)
        
        # Format and display results
        if format == 'table':
            _display_results_table(results)
        elif format == 'json':
            _display_results_json(results, output)
        elif format == 'csv':
            _display_results_csv(results, output)
        
    except Exception as e:
        click.echo(f"Error during query execution: {e}", err=True)
        if ctx.obj.get('verbose'):
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _display_results_table(results):
    """Display query results as a table."""
    result_list = list(results)
    
    if not result_list:
        click.echo("No results found.")
        return
    
    # Get variable names from first result
    if hasattr(result_list[0], 'labels'):
        headers = list(result_list[0].labels)
    else:
        headers = ['Result']
    
    click.echo(f"\nQuery Results ({len(result_list)} rows):")
    click.echo("-" * 50)
    
    # Print headers
    click.echo("\t".join(headers))
    click.echo("-" * 50)
    
    # Print rows
    for row in result_list[:100]:  # Limit to first 100 results
        if hasattr(row, 'bindings'):
            values = [str(row.get(var, '')) for var in headers]
        else:
            values = [str(row)]
        click.echo("\t".join(values))
    
    if len(result_list) > 100:
        click.echo(f"\n... and {len(result_list) - 100} more results.")


def _display_results_json(results, output_path):
    """Display query results as JSON."""
    import json
    
    result_list = []
    for row in results:
        if hasattr(row, 'bindings'):
            result_dict = {}
            for var in row.labels:
                value = row.get(var)
                result_dict[str(var)] = str(value) if value else None
            result_list.append(result_dict)
        else:
            result_list.append(str(row))
    
    json_output = json.dumps(result_list, indent=2)
    
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(json_output)
        click.echo(f"Results written to {output_path}")
    else:
        click.echo(json_output)


def _display_results_csv(results, output_path):
    """Display query results as CSV."""
    import csv
    import io
    
    result_list = list(results)
    
    if not result_list:
        click.echo("No results to export.")
        return
    
    output = io.StringIO()
    
    # Get headers
    if hasattr(result_list[0], 'labels'):
        headers = list(result_list[0].labels)
        writer = csv.writer(output)
        writer.writerow(headers)
        
        for row in result_list:
            values = [str(row.get(var, '')) for var in headers]
            writer.writerow(values)
    else:
        writer = csv.writer(output)
        writer.writerow(['Result'])
        for row in result_list:
            writer.writerow([str(row)])
    
    csv_content = output.getvalue()
    
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(csv_content)
        click.echo(f"Results written to {output_path}")
    else:
        click.echo(csv_content)


@cli.command()
@click.option('--supported-formats', is_flag=True, 
              help='Show supported export formats')
@click.option('--examples', is_flag=True, 
              help='Show usage examples')
def info(supported_formats, examples):
    """Show information about ACR Diagrams."""
    
    click.echo("ACR Diagrams - Code Analysis and Knowledge Graph Generation")
    click.echo("=" * 60)
    
    if supported_formats:
        exporter = TurtleExporter()
        format_info = exporter.get_format_info()
        
        click.echo("\nSupported Export Formats:")
        click.echo("-" * 30)
        
        for format_name, info in format_info.items():
            click.echo(f"{format_name}:")
            click.echo(f"  Name: {info['name']}")
            click.echo(f"  Description: {info['description']}")
            click.echo(f"  Extension: {info['file_extension']}")
            click.echo(f"  MIME Type: {info['mime_type']}")
            click.echo(f"  Human Readable: {info['human_readable']}")
            click.echo()
    
    if examples:
        click.echo("\nUsage Examples:")
        click.echo("-" * 20)
        
        examples_text = """
# Analyze a single C# file
acr-kg analyze MyClass.cs --output analysis.ttl --statistics

# Analyze entire Go project directory
acr-kg analyze ./src --recursive --format json-ld --output project.jsonld

# Export existing graph to multiple formats
acr-kg export analysis.ttl output --all-formats --validate --manifest

# Query the knowledge graph
acr-kg query analysis.ttl query.sparql --format table

# Show information about supported formats
acr-kg info --supported-formats
        """
        
        click.echo(examples_text)


# Create the main entry point
def main():
    """Main entry point for the acr-kg command."""
    if click is None:
        print("Error: click library is required for CLI functionality")
        print("Install it with: pip install click")
        sys.exit(1)
    
    cli()


if __name__ == '__main__':
    main()