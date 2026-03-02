# New Tools Integration Plan

> **Protocol**: Follow [planning-instructions.md](../ai-context/planning-instructions.md#following-a-plan) for execution rules.
> **Created**: 2026-03-02
> **Agent**: Copilot
> **Scope**: Integrate `codemap_generator` and `md_link_checker` from `New stuff/` into the `dev_tools` package as proper sub-packages, with CLI entry points, tests, and updated packaging.

---

> ⚠️ **Execution**: Update Status column before/after each task. See [Following a Plan](../ai-context/planning-instructions.md#following-a-plan).

## Task Index

| Phase | # | Task | Details | Agent | Cost | Complexity | Est. | Refs | Status |
|-------|---|------|---------|-------|------|------------|------|------|--------|
| **0 — Setup** | 0 | Create sub-package scaffolding | [Details](#task-0-create-sub-package-scaffolding) | Copilot | 💚 | Simple | 10 min | | ✅ Done |
| **1 — md_link_checker** | 1 | Move md_link_checker into dev_tools | [Details](#task-1-move-md_link_checker-into-dev_tools) | Copilot | 💚 | Simple | 10 min | | |
| | 2 | Write tests for md_link_checker | [Details](#task-2-write-tests-for-md_link_checker) | QA Engineer | 💛 | Medium | 25 min | | |
| **2 — codemap_generator** | 3 | Refactor codemap_generator into sub-package | [Details](#task-3-refactor-codemap_generator-into-sub-package) | Copilot | 💛 | Medium | 20 min | | |
| | 4 | Generalize hardcoded references | [Details](#task-4-generalize-hardcoded-references) | Copilot | 💛 | Medium | 15 min | | |
| | 5 | Write tests for codemap_generator | [Details](#task-5-write-tests-for-codemap_generator) | QA Engineer | 💛 | Medium | 25 min | | |
| **3 — Packaging** | 6 | Update pyproject.toml and package __init__.py | [Details](#task-6-update-pyprojecttoml-and-package-__init__py) | Copilot | 💚 | Simple | 10 min | | |
| | 7 | Replace tomllib with regex parser | [Details](#task-7-replace-tomllib-with-regex-parser) | Copilot | 💚 | Simple | 10 min | | |
| **4 — Validation** | 8 | Run full test suite and lint | [Details](#task-8-run-full-test-suite-and-lint) | Copilot | 💚 | Simple | 10 min | | |
| **5 — Cleanup** | 9 | Remove New stuff folder and finalize | [Details](#task-9-remove-new-stuff-folder-and-finalize) | Librarian | 💚 | Simple | 15 min | | |

---

## Overview

The `New stuff/` folder contains two standalone tools copied from another project:

1. **`codemap_generator.py`** (~846 lines) — An AST-based Python code documentation generator that outputs markdown files (symbol index, dependency graph, entry points, call graph). Currently a single-file CLI script hardcoded to a `dw_to_ad` package.

2. **`md_link_checker/`** (4 files) — A zero-dependency markdown internal link checker. Already structured as a proper sub-package with `scanner.py` (core logic), `cli.py` (CLI + JSON output), `__main__.py` (runnable via `python -m`), and a clean `__init__.py` with full public API.

Both tools are self-contained utilities that will be integrated as sub-packages inside `src/dev_tools/`, with CLI console script entry points registered in `pyproject.toml`.

### Target Structure

```
src/
  dev_tools/
    __init__.py                  # updated — add new exports
    custom_decorators.py         # existing (unchanged)
    custom_handlers.py           # existing (unchanged)
    debug_tools.py               # existing (unchanged)
    logger_settings.py           # existing (unchanged)
    progress_bar.py              # existing (unchanged)
    md_link_checker/             # NEW — moved from New stuff/
      __init__.py
      __main__.py
      cli.py
      scanner.py
    codemap_generator/           # NEW — refactored from single file
      __init__.py                # public API exports + main()
      __main__.py                # enables `python -m dev_tools.codemap_generator`
      generator.py               # CodeMapGenerator class + dataclasses
  tests/
    __init__.py                  # existing (unchanged)
    test_custom_decorators.py    # existing (unchanged)
    test_custom_handlers.py      # existing (unchanged)
    test_debug_tools.py          # existing (unchanged)
    test_logger_settings.py      # existing (unchanged)
    test_progress_bar.py         # existing (unchanged)
    test_md_link_checker.py      # NEW
    test_codemap_generator.py    # NEW
```

---

## Task Details

---

### Task 0: Create sub-package scaffolding

**What:** Create the empty directory structure for both new sub-packages inside `src/dev_tools/`.

**Files:**
- CREATE `src/dev_tools/md_link_checker/` (directory)
- CREATE `src/dev_tools/codemap_generator/` (directory)

**Acceptance criteria:**
- Both directories exist under `src/dev_tools/`.
- No files moved yet — just the structure.

> **✅ Completed 2026-03-02**
> - Created `src/dev_tools/md_link_checker/` and `src/dev_tools/codemap_generator/` directories.
> - No files moved — structure only.
> - **Changelog:** Added — Sub-package directory scaffolding for `md_link_checker` and `codemap_generator`.

---

### Task 1: Move md_link_checker into dev_tools

**What:** Copy the 4 files from `New stuff/md_link_checker/` into `src/dev_tools/md_link_checker/`. This sub-package is already well-structured with relative imports so it should work as-is. Update the `__main__.py` module path reference if needed.

**Files:**
- CREATE `src/dev_tools/md_link_checker/__init__.py` (from `New stuff/md_link_checker/__init__.py`)
- CREATE `src/dev_tools/md_link_checker/__main__.py` (from `New stuff/md_link_checker/__main__.py`)
- CREATE `src/dev_tools/md_link_checker/cli.py` (from `New stuff/md_link_checker/cli.py`)
- CREATE `src/dev_tools/md_link_checker/scanner.py` (from `New stuff/md_link_checker/scanner.py`)

**Acceptance criteria:**
- All 4 files exist in `src/dev_tools/md_link_checker/`.
- Relative imports (`.scanner`, `.cli`) remain unchanged.
- `python -m dev_tools.md_link_checker --help` works.

---

### Task 2: Write tests for md_link_checker

**What:** Create `src/tests/test_md_link_checker.py` with pytest-style tests covering the core scanner logic: `slugify_heading`, `extract_anchors`, `find_markdown_files`, `resolve_link_target`, `check_link`, `scan_file`, and the CLI `build_parser`.

**Files:**
- CREATE `src/tests/test_md_link_checker.py`
- CREATE temporary test fixture markdown files (in a temp dir during tests via `tmp_path` fixture)

**Acceptance criteria:**
- Tests cover at least: heading slugification, anchor extraction, link resolution (relative + anchor-only), broken link detection, skipping external links, CLI parser arguments.
- All tests pass with `pytest src/tests/test_md_link_checker.py -v`.

---

### Task 3: Refactor codemap_generator into sub-package

**What:** Split the single 846-line `codemap_generator.py` into a proper sub-package:
- `generator.py` — all dataclasses (`SymbolInfo`, `ImportInfo`, `EntryPoint`, `CallInfo`) and the `CodeMapGenerator` class.
- `__init__.py` — public API exports (`CodeMapGenerator`, `SymbolInfo`, dataclasses) and re-export `main`.
- `__main__.py` — enables `python -m dev_tools.codemap_generator`, delegates to `main()`.

**Files:**
- CREATE `src/dev_tools/codemap_generator/__init__.py`
- CREATE `src/dev_tools/codemap_generator/__main__.py`
- CREATE `src/dev_tools/codemap_generator/generator.py`

**Acceptance criteria:**
- `from dev_tools.codemap_generator import CodeMapGenerator` works.
- `python -m dev_tools.codemap_generator --help` works.
- All original functionality preserved.

---

### Task 4: Generalize hardcoded references

**What:** The original `codemap_generator.py` has `dw_to_ad` hardcoded as the default package name in multiple places (CLI defaults, docstrings, output text). Generalize these so the tool works for any package:
- Change the `--package` CLI default from `"dw_to_ad"` to a required argument (or auto-detect from `pyproject.toml`).
- Remove `dw_to_ad` references from output strings — use the configured package name instead.
- Update the docstring module header to be generic.

**Files:**
- MODIFY `src/dev_tools/codemap_generator/generator.py`

**Acceptance criteria:**
- No remaining `dw_to_ad` strings anywhere in the codemap_generator sub-package.
- `--package` is either required or auto-detected.
- Running `python -m dev_tools.codemap_generator --help` shows generic description.

---

### Task 5: Write tests for codemap_generator

**What:** Create `src/tests/test_codemap_generator.py` with pytest-style tests covering: `SymbolInfo`/`ImportInfo` dataclasses, `CodeMapGenerator.analyze()` on a small fixture package, symbol extraction, import extraction, entry point detection, and output generation.

**Files:**
- CREATE `src/tests/test_codemap_generator.py`

**Acceptance criteria:**
- Tests cover at least: dataclass creation, AST analysis on a fixture file, symbol/import extraction, markdown output generation.
- All tests pass with `pytest src/tests/test_codemap_generator.py -v`.

---

### Task 6: Update pyproject.toml and package __init__.py

**What:** Wire the new sub-packages into the project packaging:

1. **`pyproject.toml`**:
   - Add console script entry points for both tools.
   - Bump version to `0.3.0`.
   - Update description to mention the new tools.

2. **`src/dev_tools/__init__.py`**:
   - Add imports: `from dev_tools.md_link_checker import scan_all` and `from dev_tools.codemap_generator import CodeMapGenerator`.
   - Update `__all__` list.
   - Update module docstring.

**Files:**
- MODIFY `pyproject.toml`
- MODIFY `src/dev_tools/__init__.py`

**Acceptance criteria:**
- `pip install .` installs the package with both new sub-packages.
- `md-link-checker --help` and `codemap-generator --help` work as console commands.
- `from dev_tools import scan_all, CodeMapGenerator` works.

**pyproject.toml console scripts to add:**
```toml
[project.scripts]
md-link-checker = "dev_tools.md_link_checker.cli:main"
codemap-generator = "dev_tools.codemap_generator:main"
```

---

### Task 7: Replace tomllib with regex parser

**What:** Remove the `tomllib` import entirely. Replace `_detect_console_scripts()` with a simple regex-based parser that reads `pyproject.toml` as plain text. The `[project.scripts]` section is simple `key = "value"` pairs, so a regex can handle the common case. If parsing fails for any reason (malformed TOML, unusual formatting, file not found), silently skip — this is a "nice to have" feature, not critical.

Approach:
1. Remove `import tomllib`.
2. Read `pyproject.toml` as UTF-8 text.
3. Find the `[project.scripts]` section with a regex.
4. Parse `name = "module.path:func"` lines until the next `[` section header.
5. Wrap everything in a broad `except Exception` so it never crashes.

```python
def _detect_console_scripts(self) -> None:
    """Detect console_scripts from pyproject.toml (best-effort regex parse)."""
    pyproject_path = self.src_root.parent / "pyproject.toml"
    try:
        content = pyproject_path.read_text(encoding="utf-8")
    except OSError:
        return

    try:
        # Find [project.scripts] section
        match = re.search(r"^\[project\.scripts\]\s*$", content, re.MULTILINE)
        if not match:
            return
        section = content[match.end():]
        # Read until next section header or EOF
        next_section = re.search(r"^\[", section, re.MULTILINE)
        if next_section:
            section = section[:next_section.start()]
        # Parse key = "value" lines
        for line_match in re.finditer(r'^\s*([\w-]+)\s*=\s*["\'](.+?)["\']', section, re.MULTILINE):
            script_name = line_match.group(1)
            script_target = line_match.group(2)
            self.entry_points.append(
                EntryPoint(
                    file_path="pyproject.toml",
                    entry_type="console_script",
                    description=f"{script_name} -> {script_target}",
                )
            )
    except Exception:  # noqa: BLE001 — best-effort, never crash
        pass
```

**Files:**
- MODIFY `src/dev_tools/codemap_generator/generator.py` (remove `tomllib`, rewrite method)

**Acceptance criteria:**
- No `tomllib` or `tomli` import anywhere in the codebase.
- No new dependencies added to `pyproject.toml`.
- Console script detection works on a standard `pyproject.toml`.
- If parsing fails, the tool continues without error.
- Works on all supported Python versions (3.10+).

---

### Task 8: Run full test suite and lint

**What:** Run the complete test suite and fix any issues. Verify the package installs and both CLI entry points work.

**Files:** (potential fixes in any of the new files)

**Acceptance criteria:**
- `pytest src/tests/ -v` — all tests pass.
- `pip install .` succeeds.
- `md-link-checker --help` prints usage.
- `codemap-generator --help` prints usage.
- `python -m dev_tools.md_link_checker --help` works.
- `python -m dev_tools.codemap_generator --help` works.

---

### Task 9: Remove New stuff folder and finalize

**What:** This is the Cleanup phase. After all integration is verified:

1. Delete the `New stuff/` folder (source files are now in `src/dev_tools/`).
2. Update `README.md` if it documents the package contents.
3. Create `CHANGELOG.md` if it doesn't exist, with an `[Unreleased]` section documenting the new tools.
4. Update any other docs that reference the package structure.
5. Final commit.

**Files:**
- DELETE `New stuff/` folder (entire directory)
- MODIFY `README.md` (add new tools documentation)
- CREATE or MODIFY `CHANGELOG.md`

**Acceptance criteria:**
- `New stuff/` folder no longer exists.
- `CHANGELOG.md` exists with entries for the new sub-packages.
- `README.md` documents both new tools.
- All tests still pass after cleanup.
- Clean commit with all changes.
