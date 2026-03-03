# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Log folder structure now uses zero-padded numeric months and days (`2026/03/02`) instead of named months (`2026/3.March/2`).

### Added

- `version.yml` CI workflow — automatic version bumping (patch on push, minor on PR merge) with changelog stamping and GitHub releases.

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
