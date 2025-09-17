"""
Setup script for ACR Diagrams package.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_path = Path(__file__).parent / "README.md"
if readme_path.exists():
    with open(readme_path, "r", encoding="utf-8") as f:
        long_description = f.read()
else:
    long_description = "ACR Diagrams - Code Analysis and Knowledge Graph Generation"

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
if requirements_path.exists():
    with open(requirements_path, "r", encoding="utf-8") as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]
else:
    requirements = [
        "rdflib>=7.0.0",
        "click>=8.0.0"
    ]

setup(
    name="acr-diagrams",
    version="1.0.0",
    author="ACR Diagrams Team",
    author_email="acr-diagrams@example.com",
    description="Code Analysis and Knowledge Graph Generation for C# and Go",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/khall-ms/acr-build-helloworld-node",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.800"
        ],
        "full": [
            "tree-sitter>=0.20.0",
            "tree-sitter-csharp>=0.20.0",
            "tree-sitter-go>=0.20.0"
        ],
    },
    entry_points={
        "console_scripts": [
            "acr-kg=acr_diagrams.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)