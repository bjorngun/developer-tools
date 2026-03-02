"""Command-line interface for the markdown link checker.

Handles argument parsing, coloured terminal output, and JSON reporting.
All scanning logic lives in :mod:`dev_tools.md_link_checker.scanner`.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import TextIO

from .scanner import LinkResult, LinkStatus, ScanResult, scan_all


# ---------------------------------------------------------------------------
# ANSI colour helpers
# ---------------------------------------------------------------------------

def _supports_color() -> bool:
    """Return ``True`` if stdout appears to support ANSI colour codes."""
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def _red(text: str, *, color: bool = True) -> str:
    return f"\033[31m{text}\033[0m" if color else text


def _green(text: str, *, color: bool = True) -> str:
    return f"\033[32m{text}\033[0m" if color else text


def _yellow(text: str, *, color: bool = True) -> str:
    return f"\033[33m{text}\033[0m" if color else text


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def _separator(text: str = "", width: int = 70) -> str:
    """Build a pytest-style separator line: ``=== text ===``."""
    if not text:
        return "=" * width
    padding = max(0, width - len(text) - 2)
    left = padding // 2
    right = padding - left
    return f"{'=' * left} {text} {'=' * right}"


def print_results(
    scan_result: ScanResult,
    verbose: bool = False,
    color: bool | None = None,
    file: TextIO | None = None,
) -> None:
    """Print scan results in a pylint/pytest-style format.

    Args:
        scan_result: The aggregated scan results to display.
        verbose: Show OK and skipped links in addition to broken.
        color: Override colour detection.  ``None`` = auto-detect.
        file: Output stream.  Defaults to ``sys.stdout``.
    """
    out = file or sys.stdout
    use_color = _supports_color() if color is None else color
    broken: list[LinkResult] = []

    for r in scan_result.results:
        loc = f"{r.source_file}:{r.line_number}"

        if r.status == LinkStatus.BROKEN:
            reason = f" -- {r.reason}" if r.reason else ""
            print(f"{loc}: {_red('BROKEN', color=use_color)} {r.target}{reason}", file=out)
            broken.append(r)
        elif r.status == LinkStatus.OK and verbose:
            print(f"{loc}: {_green('PASSED', color=use_color)} {r.target}", file=out)
        elif r.status == LinkStatus.SKIPPED and verbose:
            print(f"{loc}: {_yellow('SKIPPED', color=use_color)} {r.target}", file=out)

    # Short summary (only when there are failures)
    if broken:
        print(file=out)
        print(_separator("short summary"), file=out)
        for r in broken:
            print(
                f"{_red('BROKEN', color=use_color)} {r.source_file}:{r.line_number} -> {r.target}",
                file=out,
            )

    # Totals bar
    parts: list[str] = []
    if scan_result.links_ok:
        parts.append(_green(f"{scan_result.links_ok} passed", color=use_color))
    if scan_result.links_broken:
        parts.append(_red(f"{scan_result.links_broken} broken", color=use_color))
    if scan_result.links_skipped:
        parts.append(_yellow(f"{scan_result.links_skipped} skipped", color=use_color))

    totals = ", ".join(parts) + f" in {scan_result.files_scanned} files"
    print(_separator(totals), file=out)


def print_json(scan_result: ScanResult, file: TextIO | None = None) -> None:
    """Print scan results as JSON.

    Args:
        scan_result: The aggregated scan results to serialise.
        file: Output stream.  Defaults to ``sys.stdout``.
    """
    out = file or sys.stdout
    output = {
        "files_scanned": scan_result.files_scanned,
        "links_checked": scan_result.links_checked,
        "links_ok": scan_result.links_ok,
        "links_broken": scan_result.links_broken,
        "links_skipped": scan_result.links_skipped,
        "broken": [
            {
                "source": r.source_file,
                "line": r.line_number,
                "text": r.link_text,
                "target": r.target,
                "reason": r.reason,
            }
            for r in scan_result.results
            if r.status == LinkStatus.BROKEN
        ],
    }
    print(json.dumps(output, indent=2, ensure_ascii=False), file=out)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser (exposed for testing or extension)."""
    parser = argparse.ArgumentParser(
        description="Check markdown files for broken internal links.",
    )
    parser.add_argument(
        "--no-anchors",
        action="store_true",
        help="Skip anchor (#section) validation (only check file existence)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed output including OK and skipped links",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="output_json",
        help="Output results as JSON instead of human-readable text",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("."),
        help="Project root directory (default: current directory)",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        metavar="DIR",
        help="Additional directory names to skip (repeatable, e.g., --exclude out --exclude _site)",
    )
    parser.add_argument(
        "--root-relative",
        action="append",
        default=[],
        metavar="GLOB",
        help=(
            "Files matching these globs resolve 'src/...' paths from the project root "
            "instead of relative to the source file "
            "(e.g., --root-relative 'docs/generated/**')"
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point for the markdown link checker.

    Args:
        argv: Command-line arguments.  ``None`` uses ``sys.argv[1:]``.

    Returns:
        Exit code: 0 if no broken links, 1 if broken links found, 2 on usage error.
    """
    args = build_parser().parse_args(argv)
    use_color = not args.no_color and _supports_color()

    root = args.root.resolve()
    if not root.is_dir():
        print(f"Error: {root} is not a directory", file=sys.stderr)
        return 2

    result = scan_all(
        root,
        skip_anchors=args.no_anchors,
        root_relative_globs=args.root_relative or None,
        extra_skip_dirs=set(args.exclude) if args.exclude else None,
    )

    if args.output_json:
        print_json(result)
    else:
        print_results(result, verbose=args.verbose, color=use_color)

    return 1 if result.links_broken > 0 else 0
