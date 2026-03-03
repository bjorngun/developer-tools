"""
cli_help.py

CLI entry point that displays comprehensive usage information for the
bosos-dev-tools package.  Designed so that an agent (or human) who has
the package installed can run ``dev-tools --help`` and immediately
understand every public API, environment variable, and CLI tool without
reading the source code.
"""

import argparse
import sys
import textwrap
from importlib.metadata import version

# ── package metadata ──────────────────────────────────────────────────
_PACKAGE = "bosos-dev-tools"
_IMPORT  = "dev_tools"
_VERSION = version(_PACKAGE)

# ── detailed help sections ────────────────────────────────────────────

_OVERVIEW = f"""\
{_PACKAGE}  v{_VERSION}
Import name : {_IMPORT}
Python      : >=3.10
License     : MIT

A reusable utility library for Python developers providing logging,
decorators, debugging helpers, progress bars, a markdown link checker,
and an AST-based code map generator.

Install:
    pip install bosos-dev-tools

Quick start:
    from dev_tools import logger_setup, timing_decorator, progress_bar
"""

_API = """\
Public API  (from dev_tools import ...)
═══════════════════════════════════════

logger_setup(script_name=None)
    Set up logging (file + optional DB + optional console).
    Reads logging.conf / logging_dev.conf based on DEBUG env var.
    If script_name is provided and LOGGER_SCRIPT_FOLDERS=True,
    logs are written to {LOGGER_PATH}/{script_name}/{year}/{month}/{day}/.

is_debug_on() -> bool
    Returns True when the DEBUG env var is truthy (true/1/t/yes).

progress_bar(iterable, decimals=1, length=50, **kwargs)
    Terminal progress bar for any iterable with len().
    kwargs: prefix, suffix, fill (default "█"), print_end.
    Shows elapsed / remaining time when TIMING=True.

timing_decorator
    Decorator that prints elapsed time for the wrapped function.
    If TIMING=True and the first arg has a .logger attribute,
    logs the elapsed time as well.

LogDBHandler(db_table)  [DEPRECATED — removed in 1.0]
    logging.Handler subclass that writes log records to a SQL
    database table via pyodbc.  Used internally by logger_setup
    when LOGGER_DATABASE=True.
    Migrate to a standard logging handler or external log service.

scan_all(root, *, skip_dirs=DEFAULT_SKIP_DIRS, check_anchors=True)
    Scan all markdown files under *root* for broken internal links.
    Returns a ScanResult with per-file LinkResult objects.
    Also available as CLI: md-link-checker

CodeMapGenerator
    AST-based code map generator.  Parses a Python package and
    produces a symbol index, dependency graph, entry points, and
    call graph.  Also available as CLI: codemap-generator
"""

_ENV_VARS = """\
Environment variables
═════════════════════

Variable                Default     Purpose
──────────────────────  ──────────  ─────────────────────────────────────
DEBUG                   False       Enable debug mode (verbose logging).
TIMING                  False       Enable timing output in progress_bar
                                    and timing_decorator.
LOGGER_PATH             ./logs      Root directory for log files.
LOGGER_CONF_PATH        logging.conf      Path to logging config file.
LOGGER_CONF_DEV_PATH    logging_dev.conf  Path to dev logging config.
LOGGER_DATABASE         False       Enable database logging (LogDBHandler).
                                    [DEPRECATED — removed in 1.0]
LOGGER_DB_TABLE         python_transfer_data_log   DB table name.
                                    [DEPRECATED — removed in 1.0]
LOGGER_DAY_SPECIFIC     False       Add day-level subfolder to log path.
LOGGER_SCRIPT_FOLDERS   False       Add script-name subfolder to log path.
SCRIPT_NAME             (cwd name)  Identifier written to DB log rows.

Set variables in a .env file (python-dotenv) or export them.
"""

_CLI_TOOLS = """\
CLI tools (console scripts)
═══════════════════════════

md-link-checker
    Scan markdown files for broken internal links.
    Usage:  md-link-checker [ROOT] [--no-anchors] [--json] [--verbose]
    Python: python -m dev_tools.md_link_checker [OPTIONS]

codemap-generator
    Generate AST-based code documentation for a Python package.
    Usage:  codemap-generator [OPTIONS]
    Python: python -m dev_tools.codemap_generator [OPTIONS]

dev-tools
    This help command.
    Usage:  dev-tools [--api | --env | --cli | --examples | --all]
"""

_EXAMPLES = """\
Usage examples
══════════════

# 1. Basic logging setup
from dev_tools import logger_setup
logger_setup()                         # uses logging.conf
logger_setup("my_etl_script")         # logs to logs/my_etl_script/...

# 2. Timing a function
from dev_tools import timing_decorator

@timing_decorator
def slow_function():
    import time; time.sleep(2)

slow_function()
# prints: Elapsed time for slow_function: 2.00 seconds

# 3. Progress bar
from dev_tools import progress_bar

for item in progress_bar(range(100), prefix="Processing"):
    pass  # do work

# 4. Check debug mode
from dev_tools import is_debug_on

if is_debug_on():
    print("Debug mode is active")

# 5. Scan markdown links (library)
from pathlib import Path
from dev_tools import scan_all

result = scan_all(Path("."))
for r in result.results:
    if r.status.value == "broken":
        print(f"{r.source_file}:{r.line_number} -> {r.target} ({r.reason})")

# 6. Generate code map (library)
from dev_tools import CodeMapGenerator

gen = CodeMapGenerator()
# see codemap-generator --help for CLI usage

# 7. Database logging  [DEPRECATED — will be removed in 1.0]
#    Set these env vars (or .env file), then call logger_setup():
#      LOGGER_DATABASE=True
#      LOGGER_DB_TABLE=my_log_table
"""


def _build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the dev-tools help CLI."""
    parser = argparse.ArgumentParser(
        prog="dev-tools",
        description=textwrap.dedent(f"""\
            {_PACKAGE} v{_VERSION} — package reference and usage guide.

            Run with no arguments to see the full overview, or pick a
            section with one of the flags below."""),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version", action="version", version=f"{_PACKAGE} {_VERSION}",
    )

    group = parser.add_argument_group("sections")
    group.add_argument(
        "--api", action="store_true",
        help="Show the public Python API reference.",
    )
    group.add_argument(
        "--env", action="store_true",
        help="Show environment variables and their defaults.",
    )
    group.add_argument(
        "--cli", action="store_true",
        help="Show available CLI console scripts.",
    )
    group.add_argument(
        "--examples", action="store_true",
        help="Show usage examples (copy-paste ready).",
    )
    group.add_argument(
        "--all", action="store_true",
        help="Show every section at once.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    """Entry point for the ``dev-tools`` console script."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    show_all = args.all
    # If no section flag is given, show overview + hint
    no_section = not any([args.api, args.env, args.cli, args.examples, show_all])

    sections: list[str] = []

    if no_section or show_all:
        sections.append(_OVERVIEW)

    if args.api or show_all:
        sections.append(_API)

    if args.env or show_all:
        sections.append(_ENV_VARS)

    if args.cli or show_all:
        sections.append(_CLI_TOOLS)

    if args.examples or show_all:
        sections.append(_EXAMPLES)

    if no_section:
        sections.append(
            "Tip: use --api, --env, --cli, --examples, or --all for more detail.\n"
        )

    sys.stdout.write("\n".join(sections))


if __name__ == "__main__":
    main()
