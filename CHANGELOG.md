# Changelog

<!-- markdownlint-disable MD024 -->

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Release workflow now triggers solely on PR merge (removed the duplicate `push`-to-`main` trigger that caused two release runs to race). Version bump size is selected by PR label: none → patch (default), `release:minor` → minor, `release:major` → major.

### Fixed

- PyPI publish step is now idempotent (`twine upload --skip-existing`) and the release job no longer fails with a `400 Bad Request` when a version was already uploaded by a concurrent run.
- GitHub Release creation now uses the `gh` CLI instead of a third-party action (removes the Node 20 deprecation warning) and no longer depends on a `pr-description` artifact that could be missing.

## [1.2.1] - 2026-06-30

### Added

- README section documenting exit-code and unhandled-exception logging behavior.
- README guide for switching from a file-per-run to a single log per day, plus an argument/env-var reference table.
- `logger_setup()` keyword arguments `logger_path`, `script_folders`, `day_specific`, and `append_same_day` that mirror the `LOGGER_*` environment variables (arguments take precedence; `None` falls back to the env var).
- Optional `override` argument on `is_same_day_append_enabled()`, `is_logs_sorted_by_days()`, and `is_script_folders_enabled()`.
- Tests for the uncaught-exception hook installed by `logger_setup()`.
- Tests for the new `logger_setup()` keyword arguments and helper overrides.

### Changed

- `logger_setup()` docstring now documents the complete `LOGGER_*` environment-variable contract and a single-log-per-day recipe, so consuming agents/tools can discover the behavior from the installed package.

### Fixed

- `log_exit_code()` now reports a truthful non-zero exit code and logs the traceback when a script ends with an unhandled exception, instead of always logging `Exit code: 0` (the old check read `sys.exc_info()` at `atexit` time, after the exception had been cleared). The default `stderr` traceback is preserved.

## [1.2.0] - 2026-06-05

### Added

- `py.typed` PEP 561 marker file for type checker support.
- `__version__` attribute accessible via `from dev_tools import __version__`.
- `Homepage` URL in PyPI project metadata.
- README documentation for logging configuration file discovery and fallback behavior.
- Subprocess tests for `python -m dev_tools.md_link_checker` and `python -m dev_tools.codemap_generator` entry points.
- Tests for `is_logs_sorted_by_days()`, `log_exit_code()`, error paths in `logger_setup()`, debug-mode branch, and `_default_logging_config()` return values.

### Changed

- **Breaking:** `timing_decorator` no longer prints elapsed time by default; requires `TIMING=True` env var.
- Publish job extracted from `version.yml` to separate `publish.yml` workflow.
- CI test matrix expanded to run all Python versions (3.10–3.14) on both Windows and Ubuntu, plus macOS with Python 3.12.

### Fixed

- `progress_bar` type hint changed from `Iterable` to `Collection` to accurately reflect `len()` requirement.
- Removed duplicate `LOGGER_DAY_SPECIFIC` table row from README.
- PR merges now publish to PyPI via release-triggered `publish.yml` workflow.
- `logger_setup(script_name=...)` no longer overwrites `SCRIPT_NAME` for later calls in the same process.
- Corrected the `dev-tools` help example for `CodeMapGenerator` to show the required constructor arguments.

## [1.0.0] - 2026-03-03

### Removed

- **`LogDBHandler`** — deprecated database logging handler and `custom_handlers` module removed.
- **`pyodbc` dependency** — no longer required.
- **`is_database_logging_on()`** helper from `logger_settings`.
- **`LOGGER_DATABASE`** and **`LOGGER_DB_TABLE`** environment variables no longer supported.
- **`[handler_logdb]`** section removed from `logging.conf`.

### Changed

- Version bumped to 1.0.0 — first stable release.
- Log folder structure now uses zero-padded numeric months and days (`2026/03/02`) instead of named months (`2026/3.March/2`).

### Added

- `version.yml` CI workflow — automatic version bumping (patch on push, minor on PR merge) with changelog stamping and GitHub releases.
- Manual version change detection in `version.yml` — skips automatic bump when the version was already updated in the commit.
- Development status classifier changed from *Beta* to *Production/Stable*.

## [0.3.0] - 2026-03-02

### Added

- `md_link_checker` sub-package — scan markdown files for broken internal links (library + CLI).
- `codemap_generator` sub-package — AST-based Python code documentation generator (library + CLI).
- Console script entry points: `md-link-checker` and `codemap-generator`.
- Top-level exports: `scan_all` and `CodeMapGenerator` available via `from dev_tools import ...`.
- Comprehensive test suites: 51 tests for `md_link_checker`, 70 tests for `codemap_generator`.

### Changed

- `codemap_generator`: `--package` CLI argument is now required (no hardcoded default).
- Replaced `tomllib` import with stdlib regex-based TOML parser for `pyproject.toml` parsing.
- Updated package description to mention new tools.

## [0.2.0]

### Added

- Initial release with `custom_decorators`, `custom_handlers`, `debug_tools`, `logger_settings`, and `progress_bar` modules.
