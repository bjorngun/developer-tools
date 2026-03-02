#!/usr/bin/env python3
"""
Code Map Generator for DW-to-AD

Generates deterministic code documentation artifacts by parsing the Python AST:
- Symbol index (classes, functions, methods)
- Import/dependency graph
- Entry point detection
- Docstring extraction
- Approximate call graph

Usage:
    python scripts/build/codemap_generator.py [--output-dir docs/ai-context/generated]

Output:
    - code-map.md: Combined code map with all artifacts
    - symbol-index.md: Classes and functions with locations
    - dependency-graph.md: Import relationships between modules
    - entry-points.md: CLI scripts and main blocks

Run this script:
    - After major refactors
    - Before PRs that change module structure
    - When onboarding new developers/agents
    - As part of release documentation
"""

import ast
import argparse
import sys
import tomllib
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class SymbolInfo:
    """Information about a code symbol (class, function, method)."""

    name: str
    symbol_type: str  # 'class', 'function', 'method', 'async_function'
    file_path: str
    line_number: int
    docstring: Optional[str] = None
    parent_class: Optional[str] = None
    is_public: bool = True
    decorators: list[str] = field(default_factory=list)
    parameters: list[str] = field(default_factory=list)


@dataclass
class ImportInfo:
    """Information about an import statement."""

    module: str
    names: list[str]  # Specific names imported, or ['*'] for star import
    is_from_import: bool
    file_path: str
    line_number: int


@dataclass
class EntryPoint:
    """Information about an entry point."""

    file_path: str
    entry_type: str  # 'main_block', 'cli_script', 'console_script'
    description: Optional[str] = None


@dataclass
class CallInfo:
    """Information about a function/method call."""

    caller: str  # function/method making the call
    callee: str  # function/method being called
    file_path: str
    line_number: int


class CodeMapGenerator:
    """
    Generates code map documentation from Python source files.

    Parses AST to extract:
    - Symbols (classes, functions, methods)
    - Import relationships
    - Entry points
    - Call graph (approximate)
    """

    def __init__(self, src_root: Path, package_name: str = "dw_to_ad"):
        self.src_root = src_root
        self.package_name = package_name
        self.symbols: list[SymbolInfo] = []
        self.imports: list[ImportInfo] = []
        self.entry_points: list[EntryPoint] = []
        self.calls: list[CallInfo] = []
        self.module_docstrings: dict[str, str] = {}

    def analyze(self) -> None:
        """Analyze all Python files in the source root."""
        package_root = self.src_root / self.package_name
        if not package_root.exists():
            raise FileNotFoundError(f"Package not found: {package_root}")

        for py_file in package_root.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            self._analyze_file(py_file)

        # Also check for pyproject.toml console_scripts
        self._detect_console_scripts()

    def _analyze_file(self, file_path: Path) -> None:
        """Analyze a single Python file."""
        try:
            source = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(file_path))
        except (SyntaxError, UnicodeDecodeError) as e:
            print(f"Warning: Could not parse {file_path}: {e}", file=sys.stderr)
            return

        relative_path = file_path.relative_to(self.src_root.parent)
        rel_str = str(relative_path).replace("\\", "/")

        # Extract module docstring
        if ast.get_docstring(tree):
            module_name = self._path_to_module(file_path)
            self.module_docstrings[module_name] = ast.get_docstring(tree) or ""

        # Walk the AST
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                self._extract_class(node, rel_str)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Only top-level functions (not methods)
                if self._is_top_level(tree, node):
                    self._extract_function(node, rel_str)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                self._extract_import(node, rel_str)

        # Check for entry points
        self._detect_main_block(tree, rel_str)
        self._detect_cli_patterns(tree, rel_str)

        # Extract calls (approximate)
        self._extract_calls(tree, rel_str)

    def _is_top_level(self, tree: ast.Module, node: ast.AST) -> bool:
        """Check if a node is at the top level of the module."""
        return node in tree.body

    def _extract_class(self, node: ast.ClassDef, file_path: str) -> None:
        """Extract class and its methods."""
        is_public = not node.name.startswith("_")
        decorators = [self._get_decorator_name(d) for d in node.decorator_list]

        class_info = SymbolInfo(
            name=node.name,
            symbol_type="class",
            file_path=file_path,
            line_number=node.lineno,
            docstring=ast.get_docstring(node),
            is_public=is_public,
            decorators=decorators,
        )
        self.symbols.append(class_info)

        # Extract methods
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method_is_public = not item.name.startswith("_") or item.name in (
                    "__init__",
                    "__call__",
                    "__enter__",
                    "__exit__",
                )
                method_decorators = [
                    self._get_decorator_name(d) for d in item.decorator_list
                ]
                params = self._extract_parameters(item)

                method_info = SymbolInfo(
                    name=item.name,
                    symbol_type="async_method"
                    if isinstance(item, ast.AsyncFunctionDef)
                    else "method",
                    file_path=file_path,
                    line_number=item.lineno,
                    docstring=ast.get_docstring(item),
                    parent_class=node.name,
                    is_public=method_is_public,
                    decorators=method_decorators,
                    parameters=params,
                )
                self.symbols.append(method_info)

    def _extract_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef, file_path: str) -> None:
        """Extract a top-level function."""
        is_public = not node.name.startswith("_")
        decorators = [self._get_decorator_name(d) for d in node.decorator_list]
        params = self._extract_parameters(node)

        func_info = SymbolInfo(
            name=node.name,
            symbol_type="async_function"
            if isinstance(node, ast.AsyncFunctionDef)
            else "function",
            file_path=file_path,
            line_number=node.lineno,
            docstring=ast.get_docstring(node),
            is_public=is_public,
            decorators=decorators,
            parameters=params,
        )
        self.symbols.append(func_info)

    def _extract_parameters(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
        """Extract parameter names from a function."""
        params = []
        for arg in node.args.args:
            if arg.arg != "self" and arg.arg != "cls":
                params.append(arg.arg)
        return params

    def _get_decorator_name(self, decorator: ast.expr) -> str:
        """Get the name of a decorator."""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return f"{self._get_full_attr(decorator)}"
        elif isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Name):
                return decorator.func.id
            elif isinstance(decorator.func, ast.Attribute):
                return self._get_full_attr(decorator.func)
        return "unknown"

    def _get_full_attr(self, node: ast.Attribute) -> str:
        """Get full attribute path like 'module.attr'."""
        parts = []
        current = node
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        return ".".join(reversed(parts))

    def _extract_import(self, node: ast.Import | ast.ImportFrom, file_path: str) -> None:
        """Extract import information."""
        if isinstance(node, ast.Import):
            for alias in node.names:
                self.imports.append(
                    ImportInfo(
                        module=alias.name,
                        names=[alias.asname or alias.name],
                        is_from_import=False,
                        file_path=file_path,
                        line_number=node.lineno,
                    )
                )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            names = [alias.name for alias in node.names]
            self.imports.append(
                ImportInfo(
                    module=module,
                    names=names,
                    is_from_import=True,
                    file_path=file_path,
                    line_number=node.lineno,
                )
            )

    def _detect_main_block(self, tree: ast.Module, file_path: str) -> None:
        """Detect if __name__ == '__main__' blocks."""
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                # Check for: if __name__ == "__main__"
                if self._is_main_check(node.test):
                    self.entry_points.append(
                        EntryPoint(
                            file_path=file_path,
                            entry_type="main_block",
                            description=f"Main block at line {node.lineno}",
                        )
                    )

    def _is_main_check(self, test: ast.expr) -> bool:
        """Check if an expression is __name__ == '__main__'."""
        if isinstance(test, ast.Compare):
            if len(test.ops) == 1 and isinstance(test.ops[0], ast.Eq):
                left = test.left
                right = test.comparators[0] if test.comparators else None
                if isinstance(left, ast.Name) and left.id == "__name__":
                    if isinstance(right, ast.Constant) and right.value == "__main__":
                        return True
        return False

    def _detect_cli_patterns(self, tree: ast.Module, file_path: str) -> None:
        """Detect CLI patterns like argparse, click, typer."""
        source_lower = ""
        try:
            source_lower = Path(self.src_root.parent / file_path).read_text().lower()
        except (FileNotFoundError, UnicodeDecodeError):
            return

        cli_indicators = ["argparse", "argumentparser", "click.command", "typer", "@app.command"]
        for indicator in cli_indicators:
            if indicator in source_lower:
                self.entry_points.append(
                    EntryPoint(
                        file_path=file_path,
                        entry_type="cli_script",
                        description=f"CLI script (detected: {indicator})",
                    )
                )
                break

    def _detect_console_scripts(self) -> None:
        """Detect console_scripts from pyproject.toml using tomllib."""
        pyproject_path = self.src_root.parent / "pyproject.toml"
        if not pyproject_path.exists():
            return

        try:
            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)

            # Check for [project.scripts] section
            scripts = data.get("project", {}).get("scripts", {})
            for script_name, script_target in scripts.items():
                self.entry_points.append(
                    EntryPoint(
                        file_path="pyproject.toml",
                        entry_type="console_script",
                        description=f"{script_name} -> {script_target}",
                    )
                )
        except (FileNotFoundError, tomllib.TOMLDecodeError):
            pass

    def _extract_calls(self, tree: ast.Module, file_path: str) -> None:
        """Extract function/method calls (approximate call graph)."""
        current_function: Optional[str] = None

        class CallVisitor(ast.NodeVisitor):
            def __init__(visitor_self):
                visitor_self.current_scope: list[str] = []

            def visit_FunctionDef(visitor_self, node: ast.FunctionDef):
                visitor_self.current_scope.append(node.name)
                visitor_self.generic_visit(node)
                visitor_self.current_scope.pop()

            def visit_AsyncFunctionDef(visitor_self, node: ast.AsyncFunctionDef):
                visitor_self.current_scope.append(node.name)
                visitor_self.generic_visit(node)
                visitor_self.current_scope.pop()

            def visit_ClassDef(visitor_self, node: ast.ClassDef):
                visitor_self.current_scope.append(node.name)
                visitor_self.generic_visit(node)
                visitor_self.current_scope.pop()

            def visit_Call(visitor_self, node: ast.Call):
                if visitor_self.current_scope:
                    caller = ".".join(visitor_self.current_scope)
                    callee = visitor_self._get_callee_name(node)
                    if callee and not callee.startswith(("print", "len", "str", "int", "list", "dict", "set", "tuple")):
                        self.calls.append(
                            CallInfo(
                                caller=caller,
                                callee=callee,
                                file_path=file_path,
                                line_number=node.lineno,
                            )
                        )
                visitor_self.generic_visit(node)

            def _get_callee_name(visitor_self, node: ast.Call) -> Optional[str]:
                if isinstance(node.func, ast.Name):
                    return node.func.id
                elif isinstance(node.func, ast.Attribute):
                    return node.func.attr
                return None

        visitor = CallVisitor()
        visitor.visit(tree)

    def _path_to_module(self, file_path: Path) -> str:
        """Convert file path to module name."""
        relative = file_path.relative_to(self.src_root.parent)
        parts = relative.with_suffix("").parts
        return ".".join(parts)

    # =========================================================================
    # Output Generation
    # =========================================================================

    def generate_symbol_index(self) -> str:
        """Generate the symbol index markdown."""
        lines = [
            "# Symbol Index",
            "",
            f"> Auto-generated by `codemap_generator.py` on {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "> **Do not edit manually** - regenerate with `python scripts/build/codemap_generator.py`",
            "",
            "## Classes",
            "",
            "| Class | File | Line | Description |",
            "|-------|------|------|-------------|",
        ]

        classes = [s for s in self.symbols if s.symbol_type == "class" and s.is_public]
        classes.sort(key=lambda x: (x.file_path, x.name))

        for cls in classes:
            doc = (cls.docstring or "").split("\n")[0][:60] if cls.docstring else "-"
            lines.append(f"| `{cls.name}` | [{cls.file_path}]({cls.file_path}#L{cls.line_number}) | {cls.line_number} | {doc} |")

        lines.extend([
            "",
            "## Functions",
            "",
            "| Function | File | Line | Description |",
            "|----------|------|------|-------------|",
        ])

        functions = [s for s in self.symbols if s.symbol_type in ("function", "async_function") and s.is_public]
        functions.sort(key=lambda x: (x.file_path, x.name))

        for func in functions:
            doc = (func.docstring or "").split("\n")[0][:60] if func.docstring else "-"
            func_type = "async " if "async" in func.symbol_type else ""
            lines.append(f"| `{func_type}{func.name}` | [{func.file_path}]({func.file_path}#L{func.line_number}) | {func.line_number} | {doc} |")

        lines.extend([
            "",
            "## Key Methods (Public)",
            "",
            "| Class.Method | File | Line | Description |",
            "|--------------|------|------|-------------|",
        ])

        methods = [s for s in self.symbols if s.symbol_type in ("method", "async_method") and s.is_public and s.parent_class]
        methods.sort(key=lambda x: (x.file_path, x.parent_class or "", x.name))

        for method in methods[:100]:  # Limit to avoid huge tables
            doc = (method.docstring or "").split("\n")[0][:50] if method.docstring else "-"
            lines.append(f"| `{method.parent_class}.{method.name}` | [{method.file_path}]({method.file_path}#L{method.line_number}) | {method.line_number} | {doc} |")

        if len(methods) > 100:
            lines.append(f"| ... | ... | ... | _{len(methods) - 100} more methods not shown_ |")

        return "\n".join(lines)

    def generate_dependency_graph(self) -> str:
        """Generate the dependency graph markdown."""
        lines = [
            "# Dependency Graph",
            "",
            f"> Auto-generated by `codemap_generator.py` on {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "> **Do not edit manually** - regenerate with `python scripts/build/codemap_generator.py`",
            "",
            "## Internal Dependencies",
            "",
            "Module import relationships within `dw_to_ad`:",
            "",
        ]

        # Group imports by source file
        internal_deps: dict[str, set[str]] = defaultdict(set)
        for imp in self.imports:
            if self.package_name in imp.module:
                source_module = imp.file_path.replace("/", ".").replace("\\", ".").replace(".py", "")
                internal_deps[source_module].add(imp.module)

        if internal_deps:
            lines.append("```mermaid")
            lines.append("graph TD")
            seen_edges = set()
            for source, targets in sorted(internal_deps.items()):
                source_short = source.split(".")[-1] if "." in source else source
                for target in sorted(targets):
                    target_short = target.split(".")[-1] if "." in target else target
                    edge = f"{source_short}-->{target_short}"
                    if edge not in seen_edges and source_short != target_short:
                        lines.append(f"    {source_short} --> {target_short}")
                        seen_edges.add(edge)
            lines.append("```")
        else:
            lines.append("_No internal dependencies detected._")

        lines.extend([
            "",
            "## External Dependencies",
            "",
            "Third-party packages used:",
            "",
            "| Package | Used In | Import Type |",
            "|---------|---------|-------------|",
        ])

        # Use sys.stdlib_module_names (Python 3.10+) for robust stdlib detection
        stdlib_modules = getattr(sys, "stdlib_module_names", set())

        external_deps: dict[str, list[str]] = defaultdict(list)
        for imp in self.imports:
            if not imp.module.startswith(self.package_name) and imp.module and not imp.module.startswith((".", "__")):
                top_level = imp.module.split(".")[0]
                if top_level not in stdlib_modules:
                    external_deps[top_level].append(imp.file_path)

        for pkg, files in sorted(external_deps.items()):
            unique_files = sorted(set(files))[:3]
            files_str = ", ".join(unique_files)
            if len(set(files)) > 3:
                files_str += f" (+{len(set(files)) - 3} more)"
            lines.append(f"| `{pkg}` | {files_str} | from import |")

        return "\n".join(lines)

    def generate_entry_points(self) -> str:
        """Generate the entry points markdown."""
        lines = [
            "# Entry Points",
            "",
            f"> Auto-generated by `codemap_generator.py` on {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "> **Do not edit manually** - regenerate with `python scripts/build/codemap_generator.py`",
            "",
            "## CLI Scripts",
            "",
            "Scripts that can be run from the command line:",
            "",
            "| File | Type | Description |",
            "|------|------|-------------|",
        ]

        for ep in self.entry_points:
            lines.append(f"| [{ep.file_path}]({ep.file_path}) | {ep.entry_type} | {ep.description or '-'} |")

        lines.extend([
            "",
            "## Main Blocks",
            "",
            "Files with `if __name__ == '__main__':` blocks:",
            "",
        ])

        main_blocks = [ep for ep in self.entry_points if ep.entry_type == "main_block"]
        for ep in main_blocks:
            lines.append(f"- [{ep.file_path}]({ep.file_path})")

        return "\n".join(lines)

    def generate_module_summaries(self) -> str:
        """Generate module summaries from docstrings."""
        lines = [
            "# Module Summaries",
            "",
            f"> Auto-generated by `codemap_generator.py` on {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "> **Do not edit manually** - regenerate with `python scripts/build/codemap_generator.py`",
            "",
            "## Package Structure",
            "",
        ]

        # Group files by directory
        files_by_dir: dict[str, list[tuple[str, str]]] = defaultdict(list)
        for sym in self.symbols:
            if sym.symbol_type == "class" or (sym.symbol_type == "function" and sym.is_public):
                dir_path = "/".join(sym.file_path.split("/")[:-1])
                file_name = sym.file_path.split("/")[-1]
                files_by_dir[dir_path].append((file_name, sym.file_path))

        # Also include modules with docstrings
        for module, docstring in self.module_docstrings.items():
            parts = module.replace(".", "/").split("/")
            if len(parts) > 1:
                dir_path = "/".join(parts[:-1])
                file_name = parts[-1] + ".py"
                full_path = module.replace(".", "/") + ".py"
                if (file_name, full_path) not in files_by_dir[dir_path]:
                    files_by_dir[dir_path].append((file_name, full_path))

        for dir_path in sorted(files_by_dir.keys()):
            if not dir_path:
                continue
            lines.append(f"### `{dir_path}/`")
            lines.append("")

            # Get unique files
            seen_files = set()
            for file_name, full_path in sorted(set(files_by_dir[dir_path])):
                if file_name in seen_files:
                    continue
                seen_files.add(file_name)

                # Get module docstring if available
                module_name = full_path.replace("/", ".").replace(".py", "")
                docstring = self.module_docstrings.get(module_name, "")
                summary = docstring.split("\n")[0][:80] if docstring else ""

                # Count symbols in this file
                class_count = len([s for s in self.symbols if s.file_path == full_path and s.symbol_type == "class"])
                func_count = len([s for s in self.symbols if s.file_path == full_path and s.symbol_type in ("function", "async_function")])

                symbol_info = []
                if class_count:
                    symbol_info.append(f"{class_count} class{'es' if class_count > 1 else ''}")
                if func_count:
                    symbol_info.append(f"{func_count} func{'s' if func_count > 1 else ''}")

                symbol_str = f" ({', '.join(symbol_info)})" if symbol_info else ""

                lines.append(f"- **[{file_name}]({full_path})**{symbol_str}")
                if summary:
                    lines.append(f"  - {summary}")

            lines.append("")

        return "\n".join(lines)

    def generate_call_graph(self) -> str:
        """Generate approximate call graph."""
        lines = [
            "# Call Graph (Approximate)",
            "",
            f"> Auto-generated by `codemap_generator.py` on {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "> **Do not edit manually** - regenerate with `python scripts/build/codemap_generator.py`",
            "",
            "⚠️ **Note**: This is a static analysis approximation. Dynamic calls and indirect references are not captured.",
            "",
            "## Key Relationships",
            "",
        ]

        # Group calls by caller
        calls_by_caller: dict[str, set[str]] = defaultdict(set)
        for call in self.calls:
            calls_by_caller[call.caller].add(call.callee)

        # Filter to interesting calls (class methods calling other methods)
        interesting_callers = [c for c in calls_by_caller.keys() if "." in c]

        if interesting_callers:
            lines.append("```mermaid")
            lines.append("graph LR")

            seen_edges = set()
            edge_count = 0
            for caller in sorted(interesting_callers):
                if edge_count > 50:  # Limit graph size
                    break
                callees = calls_by_caller[caller]
                caller_short = caller.split(".")[-1] if "." in caller else caller
                for callee in sorted(callees):
                    edge = f"{caller_short}-->{callee}"
                    if edge not in seen_edges and caller_short != callee:
                        lines.append(f"    {caller_short} --> {callee}")
                        seen_edges.add(edge)
                        edge_count += 1

            lines.append("```")

            if edge_count >= 50:
                lines.append("")
                lines.append(f"_Graph truncated at 50 edges. Total edges: {sum(len(v) for v in calls_by_caller.values())}_")
        else:
            lines.append("_No significant call relationships detected._")

        return "\n".join(lines)

    def generate_combined_code_map(self) -> str:
        """Generate the combined code map with all sections."""
        lines = [
            "# Code Map - DW-to-AD",
            "",
            f"> Auto-generated by `codemap_generator.py` on {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "> **Do not edit manually** - regenerate with `python scripts/build/codemap_generator.py`",
            "",
            "This document provides a machine-generated overview of the codebase structure.",
            "For business context and workflows, see [ARCHITECTURE.md](../../../ARCHITECTURE.md).",
            "",
            "---",
            "",
        ]

        # Statistics
        class_count = len([s for s in self.symbols if s.symbol_type == "class"])
        func_count = len([s for s in self.symbols if s.symbol_type in ("function", "async_function")])
        method_count = len([s for s in self.symbols if s.symbol_type in ("method", "async_method")])
        file_count = len(set(s.file_path for s in self.symbols))

        lines.extend([
            "## Quick Stats",
            "",
            f"- **Files analyzed**: {file_count}",
            f"- **Classes**: {class_count}",
            f"- **Functions**: {func_count}",
            f"- **Methods**: {method_count}",
            f"- **Entry points**: {len(self.entry_points)}",
            "",
            "---",
            "",
        ])

        # Entry points (most important for agents)
        lines.append(self.generate_entry_points())
        lines.extend(["", "---", ""])

        # Module summaries
        lines.append(self.generate_module_summaries())
        lines.extend(["", "---", ""])

        # Symbol index (abbreviated for combined view)
        lines.extend([
            "## Symbol Index (Key Classes)",
            "",
            "| Class | File | Description |",
            "|-------|------|-------------|",
        ])

        classes = [s for s in self.symbols if s.symbol_type == "class" and s.is_public]
        classes.sort(key=lambda x: x.name)

        for cls in classes[:30]:
            doc = (cls.docstring or "").split("\n")[0][:50] if cls.docstring else "-"
            lines.append(f"| `{cls.name}` | [{cls.file_path}]({cls.file_path}#L{cls.line_number}) | {doc} |")

        if len(classes) > 30:
            lines.append(f"| ... | ... | _{len(classes) - 30} more classes in [symbol-index.md](symbol-index.md)_ |")

        lines.extend(["", "---", ""])

        # Dependency graph (abbreviated)
        lines.extend([
            "## Internal Dependencies",
            "",
            "See [dependency-graph.md](dependency-graph.md) for full dependency analysis.",
            "",
        ])

        return "\n".join(lines)

    def write_outputs(self, output_dir: Path) -> list[Path]:
        """Write all generated files to the output directory."""
        output_dir.mkdir(parents=True, exist_ok=True)

        files_written = []

        outputs = [
            ("code-map.md", self.generate_combined_code_map()),
            ("symbol-index.md", self.generate_symbol_index()),
            ("dependency-graph.md", self.generate_dependency_graph()),
            ("entry-points.md", self.generate_entry_points()),
            ("module-summaries.md", self.generate_module_summaries()),
            ("call-graph.md", self.generate_call_graph()),
        ]

        for filename, content in outputs:
            file_path = output_dir / filename
            file_path.write_text(content, encoding="utf-8")
            files_written.append(file_path)
            print(f"  ✓ Generated {file_path}")

        return files_written


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate code map documentation for DW-to-AD",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/build/codemap_generator.py
    python scripts/build/codemap_generator.py --output-dir docs/ai-context/generated

Output files:
    code-map.md         Combined overview
    symbol-index.md     All classes and functions
    dependency-graph.md Import relationships
    entry-points.md     CLI scripts and main blocks
    module-summaries.md Per-module descriptions
    call-graph.md       Approximate call relationships
        """,
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("docs/ai-context/generated"),
        help="Output directory for generated files (default: docs/ai-context/generated)",
    )
    parser.add_argument(
        "--src-root",
        type=Path,
        default=Path("src"),
        help="Source root directory (default: src)",
    )
    parser.add_argument(
        "--package",
        type=str,
        default="dw_to_ad",
        help="Package name to analyze (default: dw_to_ad)",
    )

    args = parser.parse_args()

    print(f"🗺️  Code Map Generator for DW-to-AD")
    print(f"   Source: {args.src_root}/{args.package}")
    print(f"   Output: {args.output_dir}")
    print()

    generator = CodeMapGenerator(args.src_root, args.package)

    print("📊 Analyzing codebase...")
    generator.analyze()

    print(f"   Found {len(generator.symbols)} symbols")
    print(f"   Found {len(generator.imports)} imports")
    print(f"   Found {len(generator.entry_points)} entry points")
    print(f"   Found {len(generator.calls)} call relationships")
    print()

    print("📝 Generating documentation...")
    files = generator.write_outputs(args.output_dir)
    print()

    print(f"✅ Done! Generated {len(files)} files in {args.output_dir}")
    print()
    print("Next steps:")
    print("  1. Review generated files for accuracy")
    print("  2. Add human context where marked with placeholders")
    print("  3. Commit changes with: git add docs/ai-context/generated/")


if __name__ == "__main__":
    main()
