## Project Identity

- **Package name (PyPI):** `bosos-dev-tools`
- **Import name:** `dev_tools`
- **Source layout:** `src/dev_tools/` (src-layout, installed via `pip install .`)
- **Python:** `>=3.10`
- **Purpose:** Reusable utility library for Python developers — logging, decorators, debugging, progress bars, markdown link checking, code map generation, and CLI tools. Imported by multiple other projects.
- **Version:** see `version` in `pyproject.toml`

---

## 🛑 MANDATORY: Read Planning Instructions Before Multi-Task Work

**BEFORE creating or following any plan document**, read:
- [`docs/ai-context/planning-instructions.md`](../docs/ai-context/planning-instructions.md) — Task Index format, phase guidelines, plan lifecycle

Key rules (details in the planning doc):
- **Always mark tasks `✅ Done` immediately** after completion — never batch or defer.
- **Task Index stays at the top** of every plan document.
- **Every plan ends with a Cleanup phase** — extract learnings into docs, tidy for PR, then delete the plan.
- **Commit after every task.**

---

### Project Structure

```
src/
  dev_tools/          # main package
    __init__.py       # public API exports
    *.py              # top-level modules
    sub_package/      # sub-packages (e.g. md_link_checker, codemap_generator)
      __init__.py
      ...
  tests/              # all tests (pytest)
    test_*.py
```

- New modules go in `src/dev_tools/`.
- Multi-file tools go in sub-packages under `src/dev_tools/<tool_name>/`.
- Public API must be exported from `src/dev_tools/__init__.py` and listed in `__all__`.
- Sub-packages should have their own `__init__.py` with a clean public API.

---

### Coding Standards

- **Type Hints**: Mandatory for all new code.
- **Decorators**: Use `@dev_tools.timing_decorator` for performance monitoring.
- **Logging**: Use `logging.getLogger(__name__)`.
- **Formatting**: No trailing whitespace, single EOF newline, Unix (LF) line endings.
- **Docstrings**: Required for all public classes, functions, and modules.

---

### Dependencies

**Keep dependencies minimal.** This package is imported by multiple projects — every dependency here becomes a transitive dependency for all of them.

- Prefer stdlib solutions over third-party packages.
- If a feature can work without a dependency (even with reduced functionality), skip the dependency.
- Current dependencies: `python-dotenv` — do not add more without strong justification.
- Console scripts: `md-link-checker`, `codemap-generator` (registered in `pyproject.toml`).

---

### Public API (`__all__`)

Top-level exports from `dev_tools`:
- `logger_setup` — logging configuration
- `is_debug_on` — debug mode check
- `progress_bar` — iterable progress visualization
- `timing_decorator` — function execution timing
- `scan_all` — markdown link checking (`md_link_checker`)
- `CodeMapGenerator` — AST code map generation (`codemap_generator`)

---

### Testing

- **Framework:** `pytest` (tests in `src/tests/`)
- **Run tests:** `pytest src/tests/ -v`
- **Run with coverage:** `pytest src/tests/ --cov=dev_tools --cov-report=html`
- **Naming:** `test_<module_name>.py`, test classes `Test<ClassName>`, test functions `test_<behavior>`.
- **Pattern:** Each module in `dev_tools/` should have a corresponding `test_*.py` in `src/tests/`.

---

### Pre-Push Checklist

**CI requires passing tests and clean linting.** Before every push, run both:

1. **Tests:** `pytest src/tests/ -v` — all tests must pass.
2. **Linting:** `pylint src/dev_tools/` — must score 10/10 (CI fails on any warning or error).

Do not push until both checks pass locally.
