# Tests Directory

This directory contains unit tests for the ACR Diagrams package.

## Running Tests

To run the tests, install the package and its dependencies first:

```bash
pip install -r requirements.txt
pip install -e .
```

Then run the tests:

```bash
python -m pytest tests/
```

Or run a specific test file:

```bash
python tests/test_acr_diagrams.py
```

## Test Coverage

The tests cover:

- Code analysis functionality for C# and Go files
- Knowledge graph generation with RDF
- Export functionality to various formats
- Basic validation of outputs

Note: Some tests may be skipped if optional dependencies (like tree-sitter parsers) are not installed.