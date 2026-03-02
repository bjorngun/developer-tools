"""Markdown Internal Link Checker.

A self-contained, zero-dependency (stdlib only) toolkit for scanning
markdown files and reporting broken internal links.

**Quick start — as a library**::

    from md_link_checker import scan_all
    from pathlib import Path

    result = scan_all(Path("."))
    for r in result.results:
        if r.status == "broken":
            print(f"{r.source_file}:{r.line_number} -> {r.target} ({r.reason})")

**Quick start — as a CLI**::

    python -m md_link_checker --no-anchors --verbose

Modules:
    scanner — Data classes, enums, and all scanning/resolution logic.
    cli     — Argument parsing, coloured output, and JSON reporting.
"""

# Public API — import the things a library consumer would need.
from .scanner import (
    DEFAULT_SKIP_DIRS,
    LinkCheckError,
    LinkResult,
    LinkStatus,
    ScanResult,
    check_link,
    extract_anchors,
    find_markdown_files,
    resolve_link_target,
    scan_all,
    scan_file,
    scan_files,
    slugify_heading,
)

__all__ = [
    "DEFAULT_SKIP_DIRS",
    "LinkCheckError",
    "LinkResult",
    "LinkStatus",
    "ScanResult",
    "check_link",
    "extract_anchors",
    "find_markdown_files",
    "resolve_link_target",
    "scan_all",
    "scan_file",
    "scan_files",
    "slugify_heading",
]
