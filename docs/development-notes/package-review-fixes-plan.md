# Package Review Fixes Plan

> **Protocol**: Follow [planning-instructions.md](../ai-context/planning-instructions.md#following-a-plan) for execution rules.
> **Created**: 2026-03-03
> **Agent**: Mixed (see per-task assignments)
> **Scope**: Address all issues identified in the pip package review of `bosos-dev-tools` v1.0.1. Covers packaging metadata, code quality fixes, test coverage gaps, CI improvements, and documentation.

---

> ⚠️ **Execution**: Update Status column before/after each task. See [Following a Plan](../ai-context/planning-instructions.md#following-a-plan).

## Task Index

| Phase | # | Task | Details | Agent | Cost | Complexity | Est. | Refs | Status |
|-------|---|------|---------|-------|------|------------|------|------|--------|
| **0 — Packaging Metadata** | 0 | Add `py.typed` PEP 561 marker | [Details](#task-0-add-pytyped-pep-561-marker) | Janitor | 💚 | Simple | 5 min | [PEP 561](https://peps.python.org/pep-0561/) | ✅ Done |
| | 1 | Add `__version__` to `__init__.py` | [Details](#task-1-add-__version__-to-__init__py) | Janitor | 💚 | Simple | 5 min | | ✅ Done |
| | 2 | Add `Homepage` URL to `pyproject.toml` | [Details](#task-2-add-homepage-url-to-pyprojecttoml) | Janitor | 💚 | Simple | 5 min | | ✅ Done |
| | 2g | ⏩ Phase 0 Summary | [Protocol](../ai-context/planning-instructions.md#after-completing-a-phase) | Janitor | 💚 | Simple | 5 min | | ✅ Done |
| **1 — Code Quality** | 3 | Guard `timing_decorator` print | [Details](#task-3-guard-timing_decorator-print) | Copilot | 💚 | Simple | 10 min | | ✅ Done |
| | 4 | Fix `progress_bar` type hint | [Details](#task-4-fix-progress_bar-type-hint) | Copilot | 💚 | Simple | 10 min | | ✅ Done |
| | 5 | Fix README duplicate line | [Details](#task-5-fix-readme-duplicate-line) | Librarian | 💚 | Simple | 5 min | | ✅ Done |
| | 5g | ⏩ Phase 1 Summary | [Protocol](../ai-context/planning-instructions.md#after-completing-a-phase) | Copilot | 💚 | Simple | 5 min | | ✅ Done |
| **2 — Test Coverage** | 6 | Add `__main__.py` subprocess tests | [Details](#task-6-add-__main__py-subprocess-tests) | QA Engineer | 💛 | Medium | 25 min | | ✅ Done |
| | 7 | Improve `logger_settings.py` coverage | [Details](#task-7-improve-logger_settingspy-coverage) | QA Engineer | 💛 | Medium | 20 min | | ✅ Done |
| | 7g | ⏩ Phase 2 Summary | [Protocol](../ai-context/planning-instructions.md#after-completing-a-phase) | QA Engineer | 💚 | Simple | 5 min | | ✅ Done |
| **3 — CI & Documentation** | 8 | Separate publish workflow | [Details](#task-8-separate-publish-workflow) | Copilot | 💚 | Simple | 10 min | | ✅ Done |
| | 9 | Expand CI OS test matrix | [Details](#task-9-expand-ci-os-test-matrix) | Copilot | 💚 | Simple | 10 min | | ✅ Done |
| | 10 | Document `logging.conf` usage | [Details](#task-10-document-loggingconf-usage) | Librarian | 💚 | Simple | 15 min | | ✅ Done |
| | 10g | ⏩ Phase 3 Summary | [Protocol](../ai-context/planning-instructions.md#after-completing-a-phase) | Librarian | 💚 | Simple | 5 min | | ✅ Done |
| **4 — Cleanup** | 11 | Finalize, update docs, delete plan | [Details](#task-11-finalize-update-docs-delete-plan) | Librarian | 💚 | Simple | 15 min | | |

---

## Phase 0 — Packaging Metadata (Summary)

**Completed:** 2026-03-03 · Commit `0396937`

| Task | What was done |
|------|---------------|
| **Task 0** — `py.typed` marker | Created empty `src/dev_tools/py.typed` for PEP 561 compliance. |
| **Task 1** — `__version__` | Added `__version__` to `src/dev_tools/__init__.py` via `importlib.metadata.version("bosos-dev-tools")`. Added to `__all__`. |
| **Task 2** — Homepage URL | Added `Homepage` to `[project.urls]` in `pyproject.toml`. |

**Decisions:** Used `importlib.metadata` (stdlib, no new dependency) rather than hard-coding the version string.

**Issues:** None.

**Notes for future phases:** None.

**Changelog notes:**
- **Added** — `py.typed` PEP 561 marker file for type checker support.
- **Added** — `__version__` attribute accessible via `from dev_tools import __version__`.
- **Added** — `Homepage` URL in PyPI project metadata.

---

## Phase 1 — Code Quality (Summary)

**Completed:** 2026-03-03 · Commit `ddc37a5`

| Task | What was done |
|------|---------------|
| **Task 3** — Guard `timing_decorator` print | Wrapped both `print()` and `logger.info()` inside `if is_timing_on()` so no output is produced unless `TIMING=True`. Updated docstring. Rewrote tests to cover timing-off (no print), timing-on (prints), and logger-available (logs) scenarios. |
| **Task 4** — Fix `progress_bar` type hint | Changed `iterable` parameter type from `Iterable` to `Collection` (from `collections.abc`). `Collection` is `Sized + Iterable + Container`, correctly reflecting the `len()` call. Updated docstring. |
| **Task 5** — Fix README duplicate line | Removed stray `LOGGER_DAY_SPECIFIC` table row that appeared under the `### Markdown Link Checker` heading outside any table context. |

**Decisions:** Used `collections.abc.Collection` rather than a custom protocol — simpler and sufficient since `Collection = Sized + Iterable + Container`.

**Issues:** None.

**Notes for future phases:** Task 3 is a **breaking behavioral change** — `timing_decorator` no longer prints by default. Document in changelog.

**Changelog notes:**
- **Changed** — `timing_decorator` no longer prints elapsed time by default; requires `TIMING=True` env var.
- **Fixed** — `progress_bar` type hint changed from `Iterable` to `Collection` to accurately reflect `len()` requirement.
- **Fixed** — Removed duplicate `LOGGER_DAY_SPECIFIC` table row from README.

---

## Phase 2 — Test Coverage (Summary)

**Completed:** 2026-03-03 · 199 tests pass · pylint 10/10

| Task | What was done |
|------|---------------|
| **Task 6** — `__main__.py` subprocess tests | Added `TestMainModule` class to `test_md_link_checker.py` (3 tests: `--help`, valid scan, invalid root) and `test_codemap_generator.py` (3 tests: `--help`, missing `--package`, analyze fixture package). All use `subprocess.run([sys.executable, "-m", ...])` pattern. |
| **Task 7** — `logger_settings.py` coverage | Added 5 new test classes to `test_logger_settings.py`: `TestIsLogsSortedByDays` (env var truthy/falsy), `TestLogExitCode` (exit 0 vs 1), `TestLoggerSetupErrorPaths` (mkdir failure, fileConfig failure), `TestLoggerSetupDebugMode` (debug branch with dictConfig/fileConfig), `TestDefaultLoggingConfig` (return structure, debug vs non-debug levels). |

**Decisions:** Used `subprocess.run` with `check=False` and `timeout=30` for `__main__` tests rather than importing modules directly — ensures the actual `__main__.py` entry points are exercised. Used `unittest.mock.patch` for error-path tests rather than creating real filesystem failures.

**Issues:** None.

**Notes for future phases:** None.

**Changelog notes:**
- **Added** — Subprocess tests for `python -m dev_tools.md_link_checker` and `python -m dev_tools.codemap_generator` entry points.
- **Added** — Tests for `is_logs_sorted_by_days()`, `log_exit_code()`, error paths in `logger_setup()`, debug-mode branch, and `_default_logging_config()` return values.

---

## Phase 3 — CI & Documentation (Summary)

**Completed:** 2026-03-03 · 199 tests pass · pylint 10/10

| Task | What was done |
|------|---------------|
| **Task 8** — Separate publish workflow | Created `.github/workflows/publish.yml` triggered by `release: [published]`. Removed `publish` job from `version.yml`. PR merges now correctly publish via: version-bump → tag → Release → publish.yml → PyPI. |
| **Task 9** — Expand CI OS test matrix | Changed `os` matrix from `[windows-latest]` to `[windows-latest, ubuntu-latest]` for all 5 Python versions. Added `macos-latest` with Python 3.12 via `include`. Total: 11 test jobs. |
| **Task 10** — Document `logging.conf` usage | Added "Logging Configuration File" subsection to README explaining config file discovery (`logging.conf`/`logging_dev.conf`), fallback to built-in default, and `LOGGER_CONF_PATH`/`LOGGER_CONF_DEV_PATH`/`DEBUG` env vars. |

**Decisions:** Used `include` for the single macOS entry rather than adding it to the main matrix (keeps the matrix clean). Documented logging config inline in README rather than a separate doc page (matches project style).

**Issues:** The plan file has 8 broken anchor links from Phase 0–2 task index entries pointing to headings that were condensed into summaries. These are expected and will be resolved when the plan file is deleted in Phase 4.

**Notes for future phases:** None.

**Changelog notes:**
- **Fixed** — PR merges now publish to PyPI via release-triggered `publish.yml` workflow.
- **Changed** — Publish job extracted from `version.yml` to separate `publish.yml`.
- **Changed** — CI test matrix expanded to run all Python versions (3.10–3.14) on both Windows and Ubuntu, plus macOS with Python 3.12.
- **Added** — README documentation for logging configuration file discovery and fallback behavior.

---

## Phase 4 — Cleanup

### Task 11: Finalize, update docs, delete plan

**What:** Final cleanup phase per [Completing a Plan](../ai-context/planning-instructions.md#completing-a-plan-final-phase).

**Steps:**
1. Compile all per-phase changelog notes into `CHANGELOG.md` under `## [Unreleased]`.
2. Verify all Task Index items are `✅ Done`.
3. Run `pytest src/tests/ -v` — all tests pass.
4. Run `pylint src/dev_tools/` — 10/10.
5. Run `md-link-checker` — no broken links.
6. Update any docs that reference changed behavior (e.g., `cli_help.py` if `timing_decorator` behavior changed).
7. Delete this plan file.
8. Final commit.

**Files:**
- Modify: `CHANGELOG.md`
- Delete: `docs/development-notes/package-review-fixes-plan.md`

**Acceptance criteria:**
- All checks pass (tests, lint, link checker).
- `CHANGELOG.md` has accurate `[Unreleased]` entry.
- Plan file is deleted.
- Clean commit ready for push.
