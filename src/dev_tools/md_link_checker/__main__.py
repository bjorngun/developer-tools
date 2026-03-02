"""Allow running as ``python -m dev_tools.md_link_checker``."""

import sys

from .cli import main

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]

sys.exit(main())
