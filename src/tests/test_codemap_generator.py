"""Tests for the dev_tools.codemap_generator sub-package."""

import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Generator

import pytest

from dev_tools.codemap_generator import (
    CallInfo,
    CodeMapGenerator,
    EntryPoint,
    ImportInfo,
    SymbolInfo,
    main,
)


# ===================================================================
# Shared Fixtures
# ===================================================================


def _create_fixture_package(base: Path) -> Path:
    """Create a small fixture package under *base*/src/my_test_pkg.

    Returns the ``src`` directory (i.e. the src_root for CodeMapGenerator).
    """
    src = base / "src"
    pkg = src / "my_test_pkg"
    pkg.mkdir(parents=True)

    (pkg / "__init__.py").write_text(
        textwrap.dedent('''\
            """my_test_pkg — a fixture package for testing."""
        '''),
        encoding="utf-8",
    )

    (pkg / "models.py").write_text(
        textwrap.dedent('''\
            """Models module."""


            class MyModel:
                """A sample model."""

                def __init__(self, name: str):
                    self.name = name

                def process(self) -> str:
                    """Process the model."""
                    return self.name


            def helper_function(x: int, y: int) -> int:
                """Add two numbers."""
                return x + y


            def _private_helper():
                pass
        '''),
        encoding="utf-8",
    )

    (pkg / "utils.py").write_text(
        textwrap.dedent('''\
            """Utilities module."""
            import os
            from my_test_pkg.models import MyModel


            def run():
                model = MyModel("test")
                model.process()


            if __name__ == "__main__":
                run()
        '''),
        encoding="utf-8",
    )

    return src


@pytest.fixture()
def fixture_pkg(tmp_path: Path) -> Path:
    """Create a fixture package and return the *src_root* path."""
    return _create_fixture_package(tmp_path)


@pytest.fixture()
def analyzed_generator(fixture_pkg: Path) -> CodeMapGenerator:
    """Return a ``CodeMapGenerator`` that has already called ``analyze()``."""
    gen = CodeMapGenerator(fixture_pkg, "my_test_pkg")
    gen.analyze()
    return gen


# ===================================================================
# TestSymbolInfo
# ===================================================================


class TestSymbolInfo:
    """Tests for the SymbolInfo dataclass."""

    def test_required_fields(self) -> None:
        si = SymbolInfo(
            name="foo",
            symbol_type="function",
            file_path="pkg/mod.py",
            line_number=10,
        )
        assert si.name == "foo"
        assert si.symbol_type == "function"
        assert si.file_path == "pkg/mod.py"
        assert si.line_number == 10

    def test_default_values(self) -> None:
        si = SymbolInfo(
            name="bar",
            symbol_type="class",
            file_path="a.py",
            line_number=1,
        )
        assert si.docstring is None
        assert si.parent_class is None
        assert si.is_public is True
        assert si.decorators == []
        assert si.parameters == []

    def test_optional_fields(self) -> None:
        si = SymbolInfo(
            name="baz",
            symbol_type="method",
            file_path="a.py",
            line_number=5,
            docstring="A method.",
            parent_class="MyClass",
            is_public=False,
            decorators=["staticmethod"],
            parameters=["x", "y"],
        )
        assert si.docstring == "A method."
        assert si.parent_class == "MyClass"
        assert si.is_public is False
        assert si.decorators == ["staticmethod"]
        assert si.parameters == ["x", "y"]


# ===================================================================
# TestImportInfo
# ===================================================================


class TestImportInfo:
    """Tests for the ImportInfo dataclass."""

    def test_required_fields(self) -> None:
        ii = ImportInfo(
            module="os.path",
            names=["join"],
            is_from_import=True,
            file_path="a.py",
            line_number=1,
        )
        assert ii.module == "os.path"
        assert ii.names == ["join"]
        assert ii.is_from_import is True
        assert ii.file_path == "a.py"
        assert ii.line_number == 1

    def test_plain_import(self) -> None:
        ii = ImportInfo(
            module="sys",
            names=["sys"],
            is_from_import=False,
            file_path="a.py",
            line_number=2,
        )
        assert ii.is_from_import is False


# ===================================================================
# TestEntryPoint
# ===================================================================


class TestEntryPoint:
    """Tests for the EntryPoint dataclass."""

    def test_required_fields(self) -> None:
        ep = EntryPoint(
            file_path="cli.py",
            entry_type="main_block",
        )
        assert ep.file_path == "cli.py"
        assert ep.entry_type == "main_block"

    def test_default_description(self) -> None:
        ep = EntryPoint(file_path="x.py", entry_type="cli_script")
        assert ep.description is None

    def test_with_description(self) -> None:
        ep = EntryPoint(
            file_path="x.py",
            entry_type="console_script",
            description="my-tool -> pkg.cli:main",
        )
        assert ep.description == "my-tool -> pkg.cli:main"


# ===================================================================
# TestCallInfo
# ===================================================================


class TestCallInfo:
    """Tests for the CallInfo dataclass."""

    def test_required_fields(self) -> None:
        ci = CallInfo(
            caller="MyClass.run",
            callee="helper",
            file_path="mod.py",
            line_number=42,
        )
        assert ci.caller == "MyClass.run"
        assert ci.callee == "helper"
        assert ci.file_path == "mod.py"
        assert ci.line_number == 42


# ===================================================================
# TestCodeMapGeneratorAnalyze
# ===================================================================


class TestCodeMapGeneratorAnalyze:
    """Tests for CodeMapGenerator.analyze()."""

    def test_populates_symbols(self, analyzed_generator: CodeMapGenerator) -> None:
        assert len(analyzed_generator.symbols) > 0

    def test_populates_imports(self, analyzed_generator: CodeMapGenerator) -> None:
        assert len(analyzed_generator.imports) > 0

    def test_populates_entry_points(self, analyzed_generator: CodeMapGenerator) -> None:
        assert len(analyzed_generator.entry_points) > 0

    def test_populates_calls(self, analyzed_generator: CodeMapGenerator) -> None:
        assert len(analyzed_generator.calls) > 0

    def test_raises_on_missing_package(self, tmp_path: Path) -> None:
        gen = CodeMapGenerator(tmp_path / "src", "nonexistent_pkg")
        with pytest.raises(FileNotFoundError, match="Package not found"):
            gen.analyze()

    def test_skips_pycache(self, fixture_pkg: Path) -> None:
        pycache = fixture_pkg / "my_test_pkg" / "__pycache__"
        pycache.mkdir()
        (pycache / "cached.cpython-312.py").write_text("x = 1\n", encoding="utf-8")

        gen = CodeMapGenerator(fixture_pkg, "my_test_pkg")
        gen.analyze()

        file_paths = {s.file_path for s in gen.symbols}
        assert not any("__pycache__" in fp for fp in file_paths)

    def test_handles_syntax_error_gracefully(
        self, fixture_pkg: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        bad_file = fixture_pkg / "my_test_pkg" / "bad.py"
        bad_file.write_text("def broken(\n", encoding="utf-8")

        gen = CodeMapGenerator(fixture_pkg, "my_test_pkg")
        gen.analyze()  # should not raise

        captured = capsys.readouterr()
        assert "Warning" in captured.err
        assert "bad.py" in captured.err

    def test_collects_module_docstrings(
        self, analyzed_generator: CodeMapGenerator
    ) -> None:
        docstrings = analyzed_generator.module_docstrings
        assert any("Models module" in ds for ds in docstrings.values())
        assert any("Utilities module" in ds for ds in docstrings.values())


# ===================================================================
# TestSymbolExtraction
# ===================================================================


class TestSymbolExtraction:
    """Tests for class, function, and method symbol extraction."""

    def test_class_extracted(self, analyzed_generator: CodeMapGenerator) -> None:
        classes = [s for s in analyzed_generator.symbols if s.symbol_type == "class"]
        names = [c.name for c in classes]
        assert "MyModel" in names

    def test_class_is_public(self, analyzed_generator: CodeMapGenerator) -> None:
        my_model = next(
            s for s in analyzed_generator.symbols if s.name == "MyModel"
        )
        assert my_model.is_public is True

    def test_class_docstring(self, analyzed_generator: CodeMapGenerator) -> None:
        my_model = next(
            s for s in analyzed_generator.symbols if s.name == "MyModel"
        )
        assert my_model.docstring == "A sample model."

    def test_method_extracted(self, analyzed_generator: CodeMapGenerator) -> None:
        methods = [s for s in analyzed_generator.symbols if s.symbol_type == "method"]
        names = [m.name for m in methods]
        assert "__init__" in names
        assert "process" in names

    def test_method_parent_class(self, analyzed_generator: CodeMapGenerator) -> None:
        init = next(
            s for s in analyzed_generator.symbols
            if s.name == "__init__" and s.symbol_type == "method"
        )
        assert init.parent_class == "MyModel"

    def test_method_parameters_exclude_self(
        self, analyzed_generator: CodeMapGenerator
    ) -> None:
        init = next(
            s for s in analyzed_generator.symbols
            if s.name == "__init__" and s.parent_class == "MyModel"
        )
        assert "self" not in init.parameters
        assert "name" in init.parameters

    def test_public_function_extracted(
        self, analyzed_generator: CodeMapGenerator
    ) -> None:
        funcs = [
            s for s in analyzed_generator.symbols if s.symbol_type == "function"
        ]
        names = [f.name for f in funcs]
        assert "helper_function" in names
        assert "run" in names

    def test_private_function_marked(
        self, analyzed_generator: CodeMapGenerator
    ) -> None:
        private = next(
            s for s in analyzed_generator.symbols if s.name == "_private_helper"
        )
        assert private.is_public is False

    def test_function_parameters(self, analyzed_generator: CodeMapGenerator) -> None:
        helper = next(
            s for s in analyzed_generator.symbols if s.name == "helper_function"
        )
        assert helper.parameters == ["x", "y"]

    def test_function_docstring(self, analyzed_generator: CodeMapGenerator) -> None:
        helper = next(
            s for s in analyzed_generator.symbols if s.name == "helper_function"
        )
        assert helper.docstring == "Add two numbers."

    def test_async_function(self, fixture_pkg: Path) -> None:
        (fixture_pkg / "my_test_pkg" / "async_mod.py").write_text(
            textwrap.dedent('''\
                """Async module."""

                async def fetch_data(url: str) -> str:
                    """Fetch data from url."""
                    return url
            '''),
            encoding="utf-8",
        )
        gen = CodeMapGenerator(fixture_pkg, "my_test_pkg")
        gen.analyze()

        async_funcs = [
            s for s in gen.symbols if s.symbol_type == "async_function"
        ]
        assert any(f.name == "fetch_data" for f in async_funcs)

    def test_decorated_function(self, fixture_pkg: Path) -> None:
        (fixture_pkg / "my_test_pkg" / "deco_mod.py").write_text(
            textwrap.dedent('''\
                import functools

                def my_decorator(f):
                    @functools.wraps(f)
                    def wrapper(*a, **kw):
                        return f(*a, **kw)
                    return wrapper

                @my_decorator
                def decorated_func():
                    pass
            '''),
            encoding="utf-8",
        )
        gen = CodeMapGenerator(fixture_pkg, "my_test_pkg")
        gen.analyze()

        decorated = next(
            s for s in gen.symbols if s.name == "decorated_func"
        )
        assert "my_decorator" in decorated.decorators

    def test_dunder_init_method_is_public(
        self, analyzed_generator: CodeMapGenerator
    ) -> None:
        """__init__ is treated as public even though it starts with _."""
        init = next(
            s for s in analyzed_generator.symbols
            if s.name == "__init__" and s.parent_class == "MyModel"
        )
        assert init.is_public is True


# ===================================================================
# TestImportExtraction
# ===================================================================


class TestImportExtraction:
    """Tests for import statement extraction."""

    def test_plain_import(self, analyzed_generator: CodeMapGenerator) -> None:
        plain = [i for i in analyzed_generator.imports if not i.is_from_import]
        modules = [i.module for i in plain]
        assert "os" in modules

    def test_from_import(self, analyzed_generator: CodeMapGenerator) -> None:
        from_imports = [i for i in analyzed_generator.imports if i.is_from_import]
        assert any(
            i.module == "my_test_pkg.models" and "MyModel" in i.names
            for i in from_imports
        )

    def test_import_line_number(self, analyzed_generator: CodeMapGenerator) -> None:
        os_import = next(
            i for i in analyzed_generator.imports if i.module == "os"
        )
        assert os_import.line_number > 0

    def test_import_file_path(self, analyzed_generator: CodeMapGenerator) -> None:
        os_import = next(
            i for i in analyzed_generator.imports if i.module == "os"
        )
        assert "utils.py" in os_import.file_path


# ===================================================================
# TestEntryPointDetection
# ===================================================================


class TestEntryPointDetection:
    """Tests for entry point detection."""

    def test_main_block_detected(self, analyzed_generator: CodeMapGenerator) -> None:
        main_blocks = [
            ep for ep in analyzed_generator.entry_points
            if ep.entry_type == "main_block"
        ]
        assert len(main_blocks) >= 1
        assert any("utils.py" in ep.file_path for ep in main_blocks)

    def test_main_block_description(
        self, analyzed_generator: CodeMapGenerator
    ) -> None:
        main_block = next(
            ep for ep in analyzed_generator.entry_points
            if ep.entry_type == "main_block"
        )
        assert "Main block at line" in (main_block.description or "")

    def test_cli_pattern_argparse(self, fixture_pkg: Path) -> None:
        (fixture_pkg / "my_test_pkg" / "cli_mod.py").write_text(
            textwrap.dedent('''\
                """CLI module."""
                import argparse

                def main():
                    parser = argparse.ArgumentParser()
                    parser.add_argument("--name")
                    args = parser.parse_args()
            '''),
            encoding="utf-8",
        )
        gen = CodeMapGenerator(fixture_pkg, "my_test_pkg")
        gen.analyze()

        cli_eps = [
            ep for ep in gen.entry_points if ep.entry_type == "cli_script"
        ]
        assert any("argparse" in (ep.description or "") for ep in cli_eps)

    def test_console_scripts_from_pyproject(self, fixture_pkg: Path) -> None:
        pyproject = fixture_pkg.parent / "pyproject.toml"
        pyproject.write_text(
            textwrap.dedent('''\
                [project]
                name = "my-test-pkg"
                version = "0.1.0"

                [project.scripts]
                my-tool = "my_test_pkg.cli_mod:main"
            '''),
            encoding="utf-8",
        )
        gen = CodeMapGenerator(fixture_pkg, "my_test_pkg")
        gen.analyze()

        console_eps = [
            ep for ep in gen.entry_points if ep.entry_type == "console_script"
        ]
        assert len(console_eps) == 1
        assert "my-tool" in (console_eps[0].description or "")

    def test_no_pyproject_no_console_scripts(
        self, analyzed_generator: CodeMapGenerator
    ) -> None:
        console_eps = [
            ep for ep in analyzed_generator.entry_points
            if ep.entry_type == "console_script"
        ]
        assert len(console_eps) == 0


# ===================================================================
# TestOutputGeneration
# ===================================================================


class TestOutputGeneration:
    """Tests for markdown output generation methods."""

    def test_generate_symbol_index(
        self, analyzed_generator: CodeMapGenerator
    ) -> None:
        output = analyzed_generator.generate_symbol_index()
        assert "# Symbol Index" in output
        assert "## Classes" in output
        assert "## Functions" in output
        assert "`MyModel`" in output
        assert "`helper_function`" in output

    def test_generate_dependency_graph(
        self, analyzed_generator: CodeMapGenerator
    ) -> None:
        output = analyzed_generator.generate_dependency_graph()
        assert "# Dependency Graph" in output
        assert "## Internal Dependencies" in output
        assert "## External Dependencies" in output

    def test_generate_entry_points(
        self, analyzed_generator: CodeMapGenerator
    ) -> None:
        output = analyzed_generator.generate_entry_points()
        assert "# Entry Points" in output
        assert "main_block" in output

    def test_generate_module_summaries(
        self, analyzed_generator: CodeMapGenerator
    ) -> None:
        output = analyzed_generator.generate_module_summaries()
        assert "# Module Summaries" in output
        assert "## Package Structure" in output

    def test_generate_call_graph(
        self, analyzed_generator: CodeMapGenerator
    ) -> None:
        output = analyzed_generator.generate_call_graph()
        assert "# Call Graph" in output

    def test_generate_combined_code_map(
        self, analyzed_generator: CodeMapGenerator
    ) -> None:
        output = analyzed_generator.generate_combined_code_map()
        assert "# Code Map — my_test_pkg" in output
        assert "## Quick Stats" in output
        assert "## Symbol Index (Key Classes)" in output

    def test_symbol_index_contains_methods(
        self, analyzed_generator: CodeMapGenerator
    ) -> None:
        output = analyzed_generator.generate_symbol_index()
        assert "## Key Methods (Public)" in output
        assert "process" in output

    def test_dependency_graph_internal(self, fixture_pkg: Path) -> None:
        """Internal deps show in mermaid graph when present."""
        gen = CodeMapGenerator(fixture_pkg, "my_test_pkg")
        gen.analyze()
        output = gen.generate_dependency_graph()
        assert "my_test_pkg" in output or "mermaid" in output

    def test_combined_code_map_stats(
        self, analyzed_generator: CodeMapGenerator
    ) -> None:
        output = analyzed_generator.generate_combined_code_map()
        assert "**Classes**:" in output
        assert "**Functions**:" in output
        assert "**Entry points**:" in output

    def test_private_symbols_excluded_from_public_tables(
        self, analyzed_generator: CodeMapGenerator
    ) -> None:
        """Private functions should NOT appear in the public symbol index tables."""
        output = analyzed_generator.generate_symbol_index()
        # The Functions table only lists public functions
        functions_section = output.split("## Functions")[1].split("## Key Methods")[0]
        assert "_private_helper" not in functions_section


# ===================================================================
# TestWriteOutputs
# ===================================================================


class TestWriteOutputs:
    """Tests for write_outputs()."""

    def test_creates_output_directory(
        self, analyzed_generator: CodeMapGenerator, tmp_path: Path
    ) -> None:
        out = tmp_path / "generated" / "nested"
        analyzed_generator.write_outputs(out)
        assert out.is_dir()

    def test_writes_six_files(
        self, analyzed_generator: CodeMapGenerator, tmp_path: Path
    ) -> None:
        out = tmp_path / "output"
        files = analyzed_generator.write_outputs(out)
        assert len(files) == 6

    def test_expected_filenames(
        self, analyzed_generator: CodeMapGenerator, tmp_path: Path
    ) -> None:
        out = tmp_path / "output"
        files = analyzed_generator.write_outputs(out)
        names = {f.name for f in files}
        expected = {
            "code-map.md",
            "symbol-index.md",
            "dependency-graph.md",
            "entry-points.md",
            "module-summaries.md",
            "call-graph.md",
        }
        assert names == expected

    def test_files_contain_content(
        self, analyzed_generator: CodeMapGenerator, tmp_path: Path
    ) -> None:
        out = tmp_path / "output"
        analyzed_generator.write_outputs(out)
        for md_file in out.glob("*.md"):
            content = md_file.read_text(encoding="utf-8")
            assert len(content) > 0, f"{md_file.name} is empty"

    def test_returns_path_objects(
        self, analyzed_generator: CodeMapGenerator, tmp_path: Path
    ) -> None:
        out = tmp_path / "output"
        files = analyzed_generator.write_outputs(out)
        for f in files:
            assert isinstance(f, Path)
            assert f.exists()


# ===================================================================
# TestCLI
# ===================================================================


class TestCLI:
    """Tests for the main() CLI entry point."""

    def test_help_raises_system_exit(self) -> None:
        sys.argv = ["codemap-generator", "--help"]
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

    def test_missing_package_raises_system_exit(self) -> None:
        sys.argv = ["codemap-generator"]
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code != 0

    def test_basic_run(self, fixture_pkg: Path, tmp_path: Path) -> None:
        out_dir = tmp_path / "cli_output"
        sys.argv = [
            "codemap-generator",
            "--package", "my_test_pkg",
            "--src-root", str(fixture_pkg),
            "--output-dir", str(out_dir),
        ]
        main()

        assert out_dir.is_dir()
        generated = list(out_dir.glob("*.md"))
        assert len(generated) == 6

    def test_default_src_root_and_output_dir(self, tmp_path: Path) -> None:
        """When --src-root and --output-dir are omitted, defaults are used."""
        # Create expected default structure
        default_src = tmp_path / "src"
        pkg = default_src / "mypkg"
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").write_text("", encoding="utf-8")

        import os
        original_dir = os.getcwd()
        try:
            os.chdir(tmp_path)
            sys.argv = ["codemap-generator", "--package", "mypkg"]
            main()
            default_output = tmp_path / "docs" / "ai-context" / "generated"
            assert default_output.is_dir()
        finally:
            os.chdir(original_dir)


# ===================================================================
# TestCallGraph
# ===================================================================


class TestCallGraph:
    """Tests for call graph extraction."""

    def test_calls_detected(self, analyzed_generator: CodeMapGenerator) -> None:
        callee_names = {c.callee for c in analyzed_generator.calls}
        # run() calls MyModel() and model.process()
        assert "MyModel" in callee_names or "process" in callee_names

    def test_builtin_calls_excluded(
        self, analyzed_generator: CodeMapGenerator
    ) -> None:
        callee_names = {c.callee for c in analyzed_generator.calls}
        for builtin in ("print", "len", "str", "int", "list", "dict", "set", "tuple"):
            assert builtin not in callee_names

    def test_call_has_file_path(self, analyzed_generator: CodeMapGenerator) -> None:
        for call in analyzed_generator.calls:
            assert call.file_path != ""

    def test_call_has_line_number(self, analyzed_generator: CodeMapGenerator) -> None:
        for call in analyzed_generator.calls:
            assert call.line_number > 0

    def test_call_graph_mermaid_output(self, fixture_pkg: Path) -> None:
        """When there are class method calls, the call graph contains mermaid."""
        # Create a module with class methods calling each other
        (fixture_pkg / "my_test_pkg" / "chain.py").write_text(
            textwrap.dedent('''\
                class Worker:
                    def step_one(self):
                        self.step_two()

                    def step_two(self):
                        self.finish()

                    def finish(self):
                        pass
            '''),
            encoding="utf-8",
        )
        gen = CodeMapGenerator(fixture_pkg, "my_test_pkg")
        gen.analyze()
        output = gen.generate_call_graph()
        assert "```mermaid" in output


# ===================================================================
# TestEdgeCases
# ===================================================================


class TestEdgeCases:
    """Edge-case and boundary tests."""

    def test_empty_package(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        pkg = src / "empty_pkg"
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").write_text("", encoding="utf-8")

        gen = CodeMapGenerator(src, "empty_pkg")
        gen.analyze()
        assert gen.symbols == []
        assert gen.imports == []

    def test_star_import(self, fixture_pkg: Path) -> None:
        (fixture_pkg / "my_test_pkg" / "star.py").write_text(
            "from os.path import *\n",
            encoding="utf-8",
        )
        gen = CodeMapGenerator(fixture_pkg, "my_test_pkg")
        gen.analyze()

        star_imports = [
            i for i in gen.imports
            if "*" in i.names
        ]
        assert len(star_imports) >= 1

    def test_multiple_classes_in_one_file(self, fixture_pkg: Path) -> None:
        (fixture_pkg / "my_test_pkg" / "multi.py").write_text(
            textwrap.dedent('''\
                class Alpha:
                    pass

                class Beta:
                    pass

                class _Gamma:
                    pass
            '''),
            encoding="utf-8",
        )
        gen = CodeMapGenerator(fixture_pkg, "my_test_pkg")
        gen.analyze()

        multi_classes = [
            s for s in gen.symbols
            if s.symbol_type == "class" and "multi.py" in s.file_path
        ]
        names = {c.name for c in multi_classes}
        assert names == {"Alpha", "Beta", "_Gamma"}
        gamma = next(c for c in multi_classes if c.name == "_Gamma")
        assert gamma.is_public is False

    def test_nested_subdirectory(self, fixture_pkg: Path) -> None:
        sub = fixture_pkg / "my_test_pkg" / "sub"
        sub.mkdir()
        (sub / "__init__.py").write_text("", encoding="utf-8")
        (sub / "deep.py").write_text(
            textwrap.dedent('''\
                def deep_func():
                    """Deeply nested."""
                    pass
            '''),
            encoding="utf-8",
        )
        gen = CodeMapGenerator(fixture_pkg, "my_test_pkg")
        gen.analyze()

        deep = next(
            (s for s in gen.symbols if s.name == "deep_func"), None
        )
        assert deep is not None
        assert deep.docstring == "Deeply nested."

    @pytest.mark.parametrize(
        "filename",
        ["__init__.py", "models.py", "utils.py"],
        ids=["init", "models", "utils"],
    )
    def test_all_fixture_files_analyzed(
        self, analyzed_generator: CodeMapGenerator, filename: str
    ) -> None:
        """Every .py file in the fixture package should appear in symbols, imports, or docstrings."""
        all_paths = (
            {s.file_path for s in analyzed_generator.symbols}
            | {i.file_path for i in analyzed_generator.imports}
            | {ep.file_path for ep in analyzed_generator.entry_points}
        )
        # Module docstrings are keyed by dotted module name, not file path
        all_modules = set(analyzed_generator.module_docstrings.keys())
        assert any(filename in p for p in all_paths) or any(
            filename.replace(".py", "") in m for m in all_modules
        )


# ===================================================================
# TestMainModule — subprocess tests for __main__.py
# ===================================================================


class TestMainModule:
    """Tests for running ``python -m dev_tools.codemap_generator``."""

    def test_help_flag_exits_zero(self) -> None:
        """--help should exit 0 and print usage information."""
        result = subprocess.run(
            [sys.executable, "-m", "dev_tools.codemap_generator", "--help"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0
        assert "usage" in result.stdout.lower()

    def test_missing_required_arg_exits_nonzero(self) -> None:
        """Running without --package should exit with code 2."""
        result = subprocess.run(
            [sys.executable, "-m", "dev_tools.codemap_generator"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 2
        assert "--package" in result.stderr

    def test_analyze_fixture_package(self, tmp_path: Path) -> None:
        """Running against a minimal package should exit 0 and produce output files."""
        src = tmp_path / "src"
        pkg = src / "test_pkg"
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").write_text('"""Test pkg."""\n', encoding="utf-8")
        (pkg / "mod.py").write_text(
            'def hello():\n    """Say hello."""\n    return "hi"\n',
            encoding="utf-8",
        )
        output_dir = tmp_path / "output"
        result = subprocess.run(
            [
                sys.executable, "-m", "dev_tools.codemap_generator",
                "--package", "test_pkg",
                "--src-root", str(src),
                "--output-dir", str(output_dir),
            ],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0
        assert output_dir.exists()
        assert (output_dir / "code-map.md").exists()
