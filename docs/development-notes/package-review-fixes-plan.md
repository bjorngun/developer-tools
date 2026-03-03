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
| | 2g | ⏩ Phase 0 Summary | [Protocol](../ai-context/planning-instructions.md#after-completing-a-phase) | Janitor | 💚 | Simple | 5 min | | |
| **1 — Code Quality** | 3 | Guard `timing_decorator` print | [Details](#task-3-guard-timing_decorator-print) | Copilot | 💚 | Simple | 10 min | | |
| | 4 | Fix `progress_bar` type hint | [Details](#task-4-fix-progress_bar-type-hint) | Copilot | 💚 | Simple | 10 min | | |
| | 5 | Fix README duplicate line | [Details](#task-5-fix-readme-duplicate-line) | Librarian | 💚 | Simple | 5 min | | |
| | 5g | ⏩ Phase 1 Summary | [Protocol](../ai-context/planning-instructions.md#after-completing-a-phase) | Copilot | 💚 | Simple | 5 min | | |
| **2 — Test Coverage** | 6 | Add `__main__.py` subprocess tests | [Details](#task-6-add-__main__py-subprocess-tests) | QA Engineer | 💛 | Medium | 25 min | | |
| | 7 | Improve `logger_settings.py` coverage | [Details](#task-7-improve-logger_settingspy-coverage) | QA Engineer | 💛 | Medium | 20 min | | |
| | 7g | ⏩ Phase 2 Summary | [Protocol](../ai-context/planning-instructions.md#after-completing-a-phase) | QA Engineer | 💚 | Simple | 5 min | | |
| **3 — CI & Documentation** | 8 | Separate publish workflow | [Details](#task-8-separate-publish-workflow) | Copilot | 💚 | Simple | 10 min | | ✅ Done |
| | 9 | Expand CI OS test matrix | [Details](#task-9-expand-ci-os-test-matrix) | Copilot | 💚 | Simple | 10 min | | |
| | 10 | Document `logging.conf` usage | [Details](#task-10-document-loggingconf-usage) | Librarian | 💚 | Simple | 15 min | | |
| | 10g | ⏩ Phase 3 Summary | [Protocol](../ai-context/planning-instructions.md#after-completing-a-phase) | Librarian | 💚 | Simple | 5 min | | |
| **4 — Cleanup** | 11 | Finalize, update docs, delete plan | [Details](#task-11-finalize-update-docs-delete-plan) | Librarian | 💚 | Simple | 15 min | | |

---

## Phase 0 — Packaging Metadata

### Task 0: Add `py.typed` PEP 561 marker

**What:** Create an empty `py.typed` marker file at `src/dev_tools/py.typed` so that type checkers (mypy, pyright, Pylance) recognize this package as typed. This is a PEP 561 requirement for packages that ship inline type hints.

**Files:**
- Create: `src/dev_tools/py.typed`

**Acceptance criteria:**
- `src/dev_tools/py.typed` exists and is empty.
- `pytest` and `pylint` still pass.

---

### Task 1: Add `__version__` to `__init__.py`

**What:** Add a `__version__` attribute to `src/dev_tools/__init__.py` using `importlib.metadata.version()` so consumers can do `from dev_tools import __version__` or `dev_tools.__version__`. Add it to `__all__` as well.

**Files:**
- Modify: `src/dev_tools/__init__.py`

**Acceptance criteria:**
- `from dev_tools import __version__` works and returns the correct version string.
- `__version__` is listed in `__all__`.
- Tests and lint pass.

---

### Task 2: Add `Homepage` URL to `pyproject.toml`

**What:** Add a `Homepage` entry to `[project.urls]` in `pyproject.toml`. PyPI displays `Homepage` prominently; currently only `Source` and `Tracker` are listed.

**Files:**
- Modify: `pyproject.toml`

**Acceptance criteria:**
- `[project.urls]` contains `Homepage = "https://github.com/bjorngun/developer-tools"`.
- Package still builds and installs.

> 🛑 **Phase complete? Do these 3 steps NOW (gate task `2g`):**
> 1. **Run tests** — `pytest src/tests/ -v`
> 2. **Write phase summary** — Replace stale task detail (What/Files/Acceptance) with a condensed summary. Keep headings + completion notes. Include: what was done, decisions, issues, notes for future phases, changelog bullets.
> 3. **Commit separately** — `git commit -m "docs: Phase 0 summary"`
>
> Full protocol: [After Completing a Phase](../ai-context/planning-instructions.md#after-completing-a-phase)

---

## Phase 1 — Code Quality

### Task 3: Guard `timing_decorator` print

**What:** The `timing_decorator` currently unconditionally calls `print()` with the elapsed time on every decorated function invocation. This is a side-effect that can surprise library consumers who just want timing when explicitly opted in. Change the `print()` call to only execute when `is_timing_on()` returns `True`.

**Why:** Library code should not produce console output by default. Users who need timing output opt in via `TIMING=True`.

**Files:**
- Modify: `src/dev_tools/custom_decorators.py`
- Modify: `src/tests/test_custom_decorators.py` (update tests to match new behavior)

**Acceptance criteria:**
- When `TIMING` env var is unset/false, `timing_decorator` does NOT print anything.
- When `TIMING=True`, elapsed time is printed (and logged if applicable).
- All existing tests pass (updated as needed).
- Pylint 10/10.

**Risks:** This is a **breaking behavioral change** for anyone relying on the unconditional print. Acceptable for a utility library where the print was arguably a bug.

---

### Task 4: Fix `progress_bar` type hint

**What:** The `progress_bar` function's `iterable` parameter is typed as `Iterable` but immediately calls `len(iterable)`, which requires `Sized`. The type hint should reflect what the function actually needs. Use `typing.Sized` in combination or a `Collection` type, or a protocol.

**Files:**
- Modify: `src/dev_tools/progress_bar.py`

**Acceptance criteria:**
- Type hint accurately reflects that `iterable` must support `len()`.
- Pylint 10/10 and all tests pass.
- A type checker would flag `progress_bar(iter([1,2,3]))` as an error.

---

### Task 5: Fix README duplicate line

**What:** In `README.md` around line 100, a stray `| \`LOGGER_DAY_SPECIFIC\` | \`False\` | Add a day subfolder (zero-padded) |` table row appears directly below the `### Markdown Link Checker` heading, outside any table context. Remove it.

**Files:**
- Modify: `README.md`

**Acceptance criteria:**
- The duplicate `LOGGER_DAY_SPECIFIC` line is removed.
- The Markdown Link Checker section reads cleanly.
- `md-link-checker` passes on the repo.

> 🛑 **Phase complete? Do these 3 steps NOW (gate task `5g`):**
> 1. **Run tests** — `pytest src/tests/ -v`
> 2. **Write phase summary** — Replace stale task detail (What/Files/Acceptance) with a condensed summary. Keep headings + completion notes. Include: what was done, decisions, issues, notes for future phases, changelog bullets.
> 3. **Commit separately** — `git commit -m "docs: Phase 1 summary"`
>
> Full protocol: [After Completing a Phase](../ai-context/planning-instructions.md#after-completing-a-phase)

---

## Phase 2 — Test Coverage

### Task 6: Add `__main__.py` subprocess tests

**What:** Both `src/dev_tools/md_link_checker/__main__.py` and `src/dev_tools/codemap_generator/__main__.py` have 0% test coverage. Add subprocess-based tests that invoke `python -m dev_tools.md_link_checker` and `python -m dev_tools.codemap_generator` and verify they produce expected output / exit codes.

**Files:**
- Modify: `src/tests/test_md_link_checker.py` (add `__main__` tests)
- Modify: `src/tests/test_codemap_generator.py` (add `__main__` tests)

**Acceptance criteria:**
- Both `__main__.py` files have >0% coverage (ideally 100% — they're typically 3-5 lines).
- All 169+ tests still pass, plus new ones.

**Notes:** Use `subprocess.run([sys.executable, "-m", "dev_tools.md_link_checker", ...])` pattern. Keep tests fast — use `--help` or minimal inputs.

---

### Task 7: Improve `logger_settings.py` coverage

**What:** `logger_settings.py` is at 84% coverage. Identify uncovered branches (likely error paths: directory creation failure, config file parse failure, fallback dict config) and add targeted tests.

**Files:**
- Modify: `src/tests/test_logger_settings.py`

**Acceptance criteria:**
- `logger_settings.py` coverage reaches ≥95%.
- All tests pass.

**Notes:** Use `unittest.mock.patch` to simulate OSError on `Path.mkdir`, missing config files, etc. Be careful with `atexit` registration — may need cleanup in tests.

> 🛑 **Phase complete? Do these 3 steps NOW (gate task `7g`):**
> 1. **Run tests** — `pytest src/tests/ -v`
> 2. **Write phase summary** — Replace stale task detail (What/Files/Acceptance) with a condensed summary. Keep headings + completion notes. Include: what was done, decisions, issues, notes for future phases, changelog bullets.
> 3. **Commit separately** — `git commit -m "docs: Phase 2 summary"`
>
> Full protocol: [After Completing a Phase](../ai-context/planning-instructions.md#after-completing-a-phase)

---

## Phase 3 — CI & Documentation

### Task 8: Separate publish workflow

**What:** Extract the `publish` job from `version.yml` into a standalone `publish.yml` triggered by `release: [published]`. This fixes a bug where PR merges created GitHub Releases but never published to PyPI (the publish job's condition excluded PR events). It also decouples publishing from versioning — publish can be re-run independently, and direct pushes no longer auto-publish.

**Files:**
- Create: `.github/workflows/publish.yml`
- Modify: `.github/workflows/version.yml` (remove `publish` job)

**Acceptance criteria:**
- `publish.yml` triggers on `release: [published]` and checks out the release tag.
- `version.yml` no longer contains a `publish` job.
- Chain: PR merge → version-bump → tag → GitHub Release → `publish.yml` → PyPI.

**Completion note (2026-03-03):**
- Created `.github/workflows/publish.yml` triggered by `release: [published]`, checks out the tag.
- Removed the `publish` job from `version.yml`.
- PR merges now correctly publish via: version-bump → tag → Release → publish.yml → PyPI.
- Direct pushes do patch bumps but no longer auto-publish (create a Release manually if needed).
- **Changelog:** Fixed — PR merges now publish to PyPI via release-triggered workflow. Changed — publish job extracted to separate `publish.yml`.

---

### Task 9: Expand CI OS test matrix

**What:** The test workflow currently runs on `windows-latest` for all 5 Python versions but only includes one `ubuntu-latest` entry (Python 3.12). Expand the matrix so all Python versions are tested on both Windows and Ubuntu. Optionally add `macos-latest` for a single Python version.

**Files:**
- Modify: `.github/workflows/test.yml`

**Acceptance criteria:**
- Matrix includes `windows-latest` and `ubuntu-latest` for all Python versions (3.10–3.14).
- Optionally `macos-latest` with Python 3.12.
- Workflow YAML is valid (can be validated with `actionlint` or a dry-run push).

---

### Task 10: Document `logging.conf` usage

**What:** The README shows `logger_setup()` but doesn't explain that it looks for `logging.conf` / `logging_dev.conf` at the CWD (or paths specified by `LOGGER_CONF_PATH` / `LOGGER_CONF_DEV_PATH`). Users who install via pip won't have these files and may not understand the fallback behavior. Add a brief section explaining:
1. Where `logger_setup` looks for config files.
2. That a sensible default dict config is used when no `.conf` file is found.
3. How to override with `LOGGER_CONF_PATH`.

**Files:**
- Modify: `README.md`

**Acceptance criteria:**
- README contains a clear explanation under the logging section about config file discovery.
- `md-link-checker` passes on the repo.

> 🛑 **Phase complete? Do these 3 steps NOW (gate task `10g`):**
> 1. **Run tests** — `pytest src/tests/ -v`
> 2. **Write phase summary** — Replace stale task detail (What/Files/Acceptance) with a condensed summary. Keep headings + completion notes. Include: what was done, decisions, issues, notes for future phases, changelog bullets.
> 3. **Commit separately** — `git commit -m "docs: Phase 3 summary"`
>
> Full protocol: [After Completing a Phase](../ai-context/planning-instructions.md#after-completing-a-phase)

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
