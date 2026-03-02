"""Markdown link scanning engine.

Pure scanning logic with zero dependencies beyond the Python stdlib.
Extracts links from markdown files, resolves them, and reports their status.
"""

import enum
import fnmatch
import logging
import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import unquote

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Default directories to skip entirely (immutable — callers can extend via parameters).
DEFAULT_SKIP_DIRS: frozenset[str] = frozenset(
    {"venv", "node_modules", ".git", "__pycache__", ".tox", "htmlcov", "dist", "build"},
)

# ---------------------------------------------------------------------------
# Compiled regex patterns
# ---------------------------------------------------------------------------

#: Inline markdown links: [text](target)
LINK_PATTERN = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")

#: Reference-style definition: [label]: target  (optionally followed by a title)
REF_DEF_PATTERN = re.compile(r'^\[([^\]]+)\]:\s+(.+?)(?:\s+["\'\'(].*)?$')

#: Reference-style usage: [text][label]  or collapsed [text][]
REF_LINK_PATTERN = re.compile(r"\[([^\]]*)\]\[([^\]]*)\]")

#: ATX-style markdown headings (## Heading)
HEADING_PATTERN = re.compile(r"^#{1,6}\s+(.+?)(?:\s*#*\s*)?$", re.MULTILINE)

#: HTML anchor IDs: <a id="..."> or <a name="...">  (legacy but common)
HTML_ANCHOR_PATTERN = re.compile(r'<a\s+(?:id|name)\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)

#: HTML heading IDs: <h1-h6 id="...">
HTML_HEADING_ID_PATTERN = re.compile(r'<h[1-6]\s+[^>]*id\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class LinkCheckError(Exception):
    """Raised when a file cannot be read during link checking.

    Attributes:
        path: The file that could not be read.
    """

    def __init__(self, path: Path, cause: OSError) -> None:
        self.path = path
        super().__init__(f"Cannot read {path}: {cause}")
        self.__cause__ = cause


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class LinkStatus(enum.StrEnum):
    """Status of a checked link.

    Using a ``StrEnum`` lets callers compare against plain strings
    (``result.status == "ok"``) while enabling exhaustiveness checks
    in ``match`` / ``if`` chains.
    """

    OK = "ok"
    BROKEN = "broken"
    SKIPPED = "skipped"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class LinkResult:
    """Result of checking a single link."""

    source_file: str
    line_number: int
    link_text: str
    target: str
    status: LinkStatus
    reason: str | None = None


@dataclass
class ScanResult:
    """Aggregate result of scanning one or more files.

    Counts are computed from ``results`` on access so they never drift
    out of sync.
    """

    files_scanned: int = 0
    results: list[LinkResult] = field(default_factory=list)

    @property
    def links_checked(self) -> int:
        return len(self.results)

    @property
    def links_ok(self) -> int:
        return sum(1 for r in self.results if r.status == LinkStatus.OK)

    @property
    def links_broken(self) -> int:
        return sum(1 for r in self.results if r.status == LinkStatus.BROKEN)

    @property
    def links_skipped(self) -> int:
        return sum(1 for r in self.results if r.status == LinkStatus.SKIPPED)


# ---------------------------------------------------------------------------
# Heading → anchor slug conversion
# ---------------------------------------------------------------------------

def slugify_heading(heading: str) -> str:
    """Convert a markdown heading to a GitHub-style anchor slug.

    Matches the behavior of GitHub's ``github-slugger`` package:
    1. Trim and lowercase.
    2. Strip inline HTML tags.
    3. Remove emoji characters.
    4. Remove punctuation (GitHub's exact set — note: ``_`` is kept).
    5. Replace each space with a hyphen (spaces are NOT collapsed).
    """
    slug = heading.strip().lower()
    # Strip inline HTML tags
    slug = re.sub(r"<[!/a-z].*?>", "", slug, flags=re.IGNORECASE)
    # Remove emoji: common emoji Unicode blocks
    slug = re.sub(
        r"[\U0001F300-\U0001F9FF\U00002702-\U000027B0\U000024C2-\U0001F251"
        r"\u2600-\u26FF\u2700-\u27BF\uFE00-\uFE0F\u200D"
        r"\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF"
        r"\u2705\u274C\u274E\u2B50\u23F0-\u23FA"
        r"\U0001F600-\U0001F64F]+",
        "",
        slug,
    )
    # Remove punctuation — GitHub's exact character set.
    # NOTE: _ (underscore) is intentionally NOT removed.
    slug = re.sub(
        r"[\u2000-\u206F\u2E00-\u2E7F'\"!#$%&()*+,./:;<=>?@\[\]^`{|}~\\]",
        "",
        slug,
    )
    # Replace each space with a hyphen individually (do NOT collapse).
    slug = slug.strip().replace(" ", "-")
    # Remove leading/trailing hyphens
    slug = slug.strip("-")
    return slug


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _iter_non_fenced_lines(content: str) -> Iterator[tuple[int, str]]:
    """Yield ``(line_number, line)`` pairs for lines outside fenced code blocks.

    Fenced blocks opened by ``` or ~~~ are tracked and their contents
    (including the fence markers themselves) are skipped.
    """
    in_fence = False
    for line_num, line in enumerate(content.splitlines(), start=1):
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            continue
        if not in_fence:
            yield line_num, line


def _is_template_placeholder(target: str) -> bool:
    """Check if a link target contains template placeholders like {NN}."""
    return "{" in target and "}" in target


# ---------------------------------------------------------------------------
# Anchor extraction
# ---------------------------------------------------------------------------

def extract_anchors(file_path: Path) -> set[str]:
    """Extract all heading anchors from a markdown file.

    Skips headings inside fenced code blocks to avoid phantom anchors
    from code examples.

    Duplicate headings are disambiguated with ``-1``, ``-2``, … suffixes
    matching GitHub's ``github-slugger`` behaviour.  For example, three
    ``## Example`` headings produce anchors ``example``, ``example-1``,
    and ``example-2``.

    Raises:
        LinkCheckError: If the file cannot be read.
    """
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise LinkCheckError(file_path, exc) from exc

    anchors: set[str] = set()
    slug_counts: dict[str, int] = {}

    for _line_num, line in _iter_non_fenced_lines(content):
        heading_match = HEADING_PATTERN.match(line)
        if heading_match:
            base_slug = slugify_heading(heading_match.group(1).strip())
            count = slug_counts.get(base_slug, 0)
            slug_counts[base_slug] = count + 1
            anchors.add(base_slug if count == 0 else f"{base_slug}-{count}")

        for html_match in HTML_ANCHOR_PATTERN.finditer(line):
            anchors.add(html_match.group(1))
        for html_match in HTML_HEADING_ID_PATTERN.finditer(line):
            anchors.add(html_match.group(1))

    return anchors


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------

def _should_skip_dir(path: Path, skip_dirs: frozenset[str]) -> bool:
    """Check if any path component is in the skip list."""
    return any(part in skip_dirs for part in path.parts)


def find_markdown_files(
    root: Path,
    skip_dirs: frozenset[str] = DEFAULT_SKIP_DIRS,
) -> list[Path]:
    """Find all markdown files under *root*, excluding ignored directories."""
    return sorted(
        f for f in root.rglob("*.md")
        if not _should_skip_dir(f.relative_to(root), skip_dirs)
    )


# ---------------------------------------------------------------------------
# Link resolution
# ---------------------------------------------------------------------------

def resolve_link_target(
    source_file: Path,
    target: str,
    root: Path,
    is_root_relative: bool,
) -> tuple[Path, str | None]:
    """Resolve a link target to an absolute file path and optional anchor.

    Args:
        source_file: The markdown file containing the link.
        target: The raw link target string.
        root: The project root directory.
        is_root_relative: Whether the source file should resolve ``src/``
            prefixed paths from the project root instead of relative to
            the source file.

    Returns:
        ``(resolved_path, anchor)`` — *anchor* is ``None`` when the link
        has no ``#`` fragment.
    """
    target = unquote(target)

    if "#" in target:
        file_part, anchor = target.split("#", 1)
    else:
        file_part, anchor = target, None

    if not file_part:
        # Anchor-only link (#section) — refers to same file
        return source_file, anchor

    if is_root_relative and file_part.startswith("src/"):
        resolved = (root / file_part).resolve()
    else:
        resolved = (source_file.parent / file_part).resolve()

    return resolved, anchor


# ---------------------------------------------------------------------------
# Single-link checking
# ---------------------------------------------------------------------------

def check_link(
    source_file: Path,
    line_number: int,
    link_text: str,
    target: str,
    root: Path,
    is_root_relative: bool,
    anchor_cache: dict[Path, set[str]],
    *,
    skip_anchors: bool = False,
) -> LinkResult:
    """Check a single markdown link and return its status."""
    rel_source = str(source_file.relative_to(root)).replace("\\", "/")

    # Skip external links
    if target.startswith(("http://", "https://", "mailto:")):
        return LinkResult(rel_source, line_number, link_text, target, LinkStatus.SKIPPED, "external")

    # Skip template placeholders
    if _is_template_placeholder(target):
        return LinkResult(rel_source, line_number, link_text, target, LinkStatus.SKIPPED, "template placeholder")

    resolved_path, anchor = resolve_link_target(source_file, target, root, is_root_relative)

    if not resolved_path.exists():
        return LinkResult(rel_source, line_number, link_text, target, LinkStatus.BROKEN, "file not found")

    # Check anchor if specified (unless skip_anchors)
    if anchor and not skip_anchors and resolved_path.suffix.lower() == ".md":
        if resolved_path not in anchor_cache:
            anchor_cache[resolved_path] = extract_anchors(resolved_path)
        if anchor not in anchor_cache[resolved_path]:
            return LinkResult(
                rel_source, line_number, link_text, target, LinkStatus.BROKEN,
                f"anchor '#{anchor}' not found in {resolved_path.name}",
            )

    return LinkResult(rel_source, line_number, link_text, target, LinkStatus.OK)


# ---------------------------------------------------------------------------
# File scanning
# ---------------------------------------------------------------------------

def scan_file(
    md_file: Path,
    root: Path,
    anchor_cache: dict[Path, set[str]],
    skip_anchors: bool = False,
    root_relative_globs: list[str] | None = None,
) -> list[LinkResult]:
    """Scan a single markdown file for links and check them.

    Handles both inline links ``[text](target)`` and reference-style links
    ``[text][ref]`` / ``[text][]`` where a matching ``[ref]: target``
    definition exists in the same file.
    """
    results: list[LinkResult] = []
    rel_path = str(md_file.relative_to(root)).replace("\\", "/")
    is_root_relative = any(
        fnmatch.fnmatch(rel_path, glob)
        for glob in (root_relative_globs or [])
    )

    try:
        content = md_file.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise LinkCheckError(md_file, exc) from exc

    # Pass 1: collect reference definitions [label]: target
    ref_defs: dict[str, str] = {}
    for _line_num, line in _iter_non_fenced_lines(content):
        def_match = REF_DEF_PATTERN.match(line.strip())
        if def_match:
            label = def_match.group(1).strip().lower()
            target = def_match.group(2).strip().strip("<>")
            ref_defs[label] = target

    # Pass 2: find and check all links
    for line_num, line in _iter_non_fenced_lines(content):
        # Strip inline code spans to avoid matching example links
        line_without_code = re.sub(r"`[^`]+`", "", line)

        # Inline links: [text](target)
        for match in LINK_PATTERN.finditer(line_without_code):
            link_text = match.group(1)
            target = match.group(2).strip()
            results.append(check_link(
                md_file, line_num, link_text, target, root, is_root_relative, anchor_cache,
                skip_anchors=skip_anchors,
            ))

        # Reference-style links: [text][label] or collapsed [text][]
        if ref_defs:
            remaining = LINK_PATTERN.sub("", line_without_code)
            remaining = REF_DEF_PATTERN.sub("", remaining)
            for ref_match in REF_LINK_PATTERN.finditer(remaining):
                link_text = ref_match.group(1)
                label = ref_match.group(2).strip().lower() or link_text.strip().lower()
                target = ref_defs.get(label)
                if target is None:
                    continue
                results.append(check_link(
                    md_file, line_num, link_text, target, root, is_root_relative, anchor_cache,
                    skip_anchors=skip_anchors,
                ))

    return results


# ---------------------------------------------------------------------------
# Multi-file scanning
# ---------------------------------------------------------------------------

def scan_files(
    files: list[Path],
    root: Path,
    skip_anchors: bool = False,
    root_relative_globs: list[str] | None = None,
) -> ScanResult:
    """Scan a pre-built list of markdown files for broken internal links.

    Use this when you already have a specific set of files to check
    (e.g. from ``git diff``, a CI changed-files list, or a custom filter).

    Args:
        files: Markdown files to scan.
        root: Project root directory (used to resolve relative paths).
        skip_anchors: If ``True``, only check file existence (skip anchor validation).
        root_relative_globs: Globs for files that resolve ``src/`` paths from root.
    """
    anchor_cache: dict[Path, set[str]] = {}
    result = ScanResult()

    for md_file in files:
        logger.debug("Scanning %s", md_file)
        result.files_scanned += 1
        try:
            result.results.extend(
                scan_file(md_file, root, anchor_cache, skip_anchors, root_relative_globs),
            )
        except LinkCheckError:
            logger.warning("Could not read %s — skipping", md_file, exc_info=True)

    return result


def scan_all(
    root: Path,
    skip_anchors: bool = False,
    root_relative_globs: list[str] | None = None,
    extra_skip_dirs: set[str] | None = None,
) -> ScanResult:
    """Scan all markdown files under *root* for broken internal links.

    Discovers files automatically via :func:`find_markdown_files` then
    delegates to :func:`scan_files`.

    Args:
        root: Project root directory to scan.
        skip_anchors: If ``True``, only check file existence (skip anchor validation).
        root_relative_globs: Globs for files that resolve ``src/`` paths from root.
        extra_skip_dirs: Additional directory names to skip beyond the defaults.
    """
    skip_dirs = DEFAULT_SKIP_DIRS | frozenset(extra_skip_dirs or ())
    md_files = find_markdown_files(root, skip_dirs)
    return scan_files(md_files, root, skip_anchors, root_relative_globs)
