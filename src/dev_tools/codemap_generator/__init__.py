"""
Code Map Generator — AST-based Python code documentation generator.

Generates deterministic documentation artifacts (symbol index, dependency graph,
entry points, call graph) by parsing the Python AST of an entire package.

Public API:
    CodeMapGenerator  — Main generator class
    SymbolInfo        — Dataclass for code symbols
    ImportInfo        — Dataclass for import statements
    EntryPoint        — Dataclass for entry points
    CallInfo          — Dataclass for call relationships
    main              — CLI entry point
"""

from dev_tools.codemap_generator.generator import (
    CallInfo,
    CodeMapGenerator,
    EntryPoint,
    ImportInfo,
    SymbolInfo,
    main,
)

__all__ = [
    "CallInfo",
    "CodeMapGenerator",
    "EntryPoint",
    "ImportInfo",
    "SymbolInfo",
    "main",
]
