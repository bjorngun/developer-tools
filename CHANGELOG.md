# Changelog

<!-- markdownlint-disable MD024 -->

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
