"""Tests for the dev_tools.md_link_checker sub-package."""

import subprocess
import sys
from pathlib import Path

import pytest

from dev_tools.md_link_checker.scanner import (
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
from dev_tools.md_link_checker.cli import build_parser, main


# ===================================================================
# TestSlugifyHeading
# ===================================================================

class TestSlugifyHeading:
    """Tests for slugify_heading."""

    @pytest.mark.parametrize(
        ("heading", "expected"),
        [
            ("Hello World", "hello-world"),
            ("Heading with punctuation! (yes)", "heading-with-punctuation-yes"),
            ("Contains <em>HTML</em> tags", "contains-html-tags"),
            ("Underscore_kept here", "underscore_kept-here"),
            ("Multiple   spaces   here", "multiple---spaces---here"),
            ("Simple", "simple"),
            ("hello---world", "hello---world"),
            ("  leading trailing  ", "leading-trailing"),
        ],
        ids=[
            "basic_heading",
            "punctuation",
            "html_tags",
            "underscores_kept",
            "spaces_become_hyphens",
            "single_word",
            "existing_hyphens",
            "leading_trailing_whitespace",
        ],
    )
    def test_slugify(self, heading: str, expected: str) -> None:
        assert slugify_heading(heading) == expected

    def test_heading_with_emoji(self) -> None:
        result = slugify_heading("🚀 Rocket Launch")
        assert result == "rocket-launch"


# ===================================================================
# TestExtractAnchors
# ===================================================================

class TestExtractAnchors:
    """Tests for extract_anchors."""

    def test_multiple_headings(self, tmp_path: Path) -> None:
        md = tmp_path / "doc.md"
        md.write_text(
            "# First\n## Second\n### Third\n",
            encoding="utf-8",
        )
        anchors = extract_anchors(md)
        assert anchors == {"first", "second", "third"}

    def test_duplicate_heading_disambiguation(self, tmp_path: Path) -> None:
        md = tmp_path / "dup.md"
        md.write_text(
            "## Example\n## Example\n## Example\n",
            encoding="utf-8",
        )
        anchors = extract_anchors(md)
        assert anchors == {"example", "example-1", "example-2"}

    def test_html_anchor_ids(self, tmp_path: Path) -> None:
        md = tmp_path / "html.md"
        md.write_text(
            '# Heading\n<a id="custom-anchor">\n<a name="legacy-anchor">\n',
            encoding="utf-8",
        )
        anchors = extract_anchors(md)
        assert "heading" in anchors
        assert "custom-anchor" in anchors
        assert "legacy-anchor" in anchors

    def test_headings_in_fenced_code_ignored(self, tmp_path: Path) -> None:
        md = tmp_path / "fenced.md"
        md.write_text(
            "# Real Heading\n```\n# Fake Heading\n```\n## Another Real\n",
            encoding="utf-8",
        )
        anchors = extract_anchors(md)
        assert "real-heading" in anchors
        assert "another-real" in anchors
        assert "fake-heading" not in anchors

    def test_html_heading_with_id(self, tmp_path: Path) -> None:
        md = tmp_path / "htmlh.md"
        md.write_text(
            '<h2 id="my-section">My Section</h2>\n',
            encoding="utf-8",
        )
        anchors = extract_anchors(md)
        assert "my-section" in anchors

    def test_unreadable_file_raises_link_check_error(self, tmp_path: Path) -> None:
        fake = tmp_path / "nonexistent.md"
        with pytest.raises(LinkCheckError):
            extract_anchors(fake)


# ===================================================================
# TestFindMarkdownFiles
# ===================================================================

class TestFindMarkdownFiles:
    """Tests for find_markdown_files."""

    def test_finds_md_files(self, tmp_path: Path) -> None:
        (tmp_path / "a.md").write_text("# A\n")
        (tmp_path / "sub").mkdir()
        (tmp_path / "sub" / "b.md").write_text("# B\n")
        (tmp_path / "other.txt").write_text("not markdown\n")

        files = find_markdown_files(tmp_path)
        names = {f.name for f in files}
        assert names == {"a.md", "b.md"}

    def test_skips_default_dirs(self, tmp_path: Path) -> None:
        (tmp_path / "good.md").write_text("# Good\n")
        for skip_dir in ("venv", "node_modules", ".git", "__pycache__"):
            d = tmp_path / skip_dir
            d.mkdir()
            (d / "hidden.md").write_text("# Hidden\n")

        files = find_markdown_files(tmp_path)
        names = {f.name for f in files}
        assert names == {"good.md"}

    def test_respects_custom_skip_dirs(self, tmp_path: Path) -> None:
        (tmp_path / "keep.md").write_text("# Keep\n")
        d = tmp_path / "skipme"
        d.mkdir()
        (d / "skipped.md").write_text("# Skipped\n")

        custom = DEFAULT_SKIP_DIRS | frozenset({"skipme"})
        files = find_markdown_files(tmp_path, skip_dirs=custom)
        names = {f.name for f in files}
        assert names == {"keep.md"}

    def test_returns_sorted(self, tmp_path: Path) -> None:
        for name in ("z.md", "a.md", "m.md"):
            (tmp_path / name).write_text(f"# {name}\n")
        files = find_markdown_files(tmp_path)
        assert files == sorted(files)


# ===================================================================
# TestResolveLinkTarget
# ===================================================================

class TestResolveLinkTarget:
    """Tests for resolve_link_target."""

    def test_relative_file_link(self, tmp_path: Path) -> None:
        source = tmp_path / "docs" / "page.md"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text("# Page\n")
        target_file = tmp_path / "docs" / "other.md"
        target_file.write_text("# Other\n")

        resolved, anchor = resolve_link_target(source, "other.md", tmp_path, False)
        assert resolved == target_file.resolve()
        assert anchor is None

    def test_anchor_only_link(self, tmp_path: Path) -> None:
        source = tmp_path / "file.md"
        source.write_text("# file\n")

        resolved, anchor = resolve_link_target(source, "#section", tmp_path, False)
        assert resolved == source
        assert anchor == "section"

    def test_file_plus_anchor(self, tmp_path: Path) -> None:
        source = tmp_path / "a.md"
        source.write_text("# A\n")

        resolved, anchor = resolve_link_target(source, "b.md#heading", tmp_path, False)
        assert resolved == (tmp_path / "b.md").resolve()
        assert anchor == "heading"

    def test_root_relative_src_path(self, tmp_path: Path) -> None:
        source = tmp_path / "docs" / "guide.md"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text("# Guide\n")

        resolved, anchor = resolve_link_target(
            source, "src/dev_tools/module.py", tmp_path, True,
        )
        assert resolved == (tmp_path / "src" / "dev_tools" / "module.py").resolve()
        assert anchor is None

    def test_non_root_relative_src_path(self, tmp_path: Path) -> None:
        source = tmp_path / "docs" / "guide.md"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text("# Guide\n")

        resolved, _anchor = resolve_link_target(
            source, "src/dev_tools/module.py", tmp_path, False,
        )
        # When not root-relative, resolves relative to source file
        assert resolved == (tmp_path / "docs" / "src" / "dev_tools" / "module.py").resolve()


# ===================================================================
# TestCheckLink
# ===================================================================

class TestCheckLink:
    """Tests for check_link."""

    def _make_source(self, tmp_path: Path) -> Path:
        src = tmp_path / "source.md"
        src.write_text("# Source\n")
        return src

    @pytest.mark.parametrize(
        "target",
        ["http://example.com", "https://example.com", "mailto:user@example.com"],
        ids=["http", "https", "mailto"],
    )
    def test_skips_external_links(self, tmp_path: Path, target: str) -> None:
        src = self._make_source(tmp_path)
        result = check_link(src, 1, "text", target, tmp_path, False, {})
        assert result.status == LinkStatus.SKIPPED
        assert result.reason == "external"

    def test_broken_file_not_found(self, tmp_path: Path) -> None:
        src = self._make_source(tmp_path)
        result = check_link(src, 1, "text", "missing.md", tmp_path, False, {})
        assert result.status == LinkStatus.BROKEN
        assert result.reason == "file not found"

    def test_broken_anchor(self, tmp_path: Path) -> None:
        src = self._make_source(tmp_path)
        target = tmp_path / "other.md"
        target.write_text("# Only Heading\n", encoding="utf-8")
        result = check_link(src, 1, "text", "other.md#nonexistent", tmp_path, False, {})
        assert result.status == LinkStatus.BROKEN
        assert result.reason is not None and "anchor" in result.reason

    def test_ok_for_valid_link(self, tmp_path: Path) -> None:
        src = self._make_source(tmp_path)
        target = tmp_path / "other.md"
        target.write_text("# Target\n", encoding="utf-8")
        result = check_link(src, 1, "text", "other.md", tmp_path, False, {})
        assert result.status == LinkStatus.OK

    def test_ok_for_valid_link_with_anchor(self, tmp_path: Path) -> None:
        src = self._make_source(tmp_path)
        target = tmp_path / "other.md"
        target.write_text("# Heading\n", encoding="utf-8")
        result = check_link(src, 1, "text", "other.md#heading", tmp_path, False, {})
        assert result.status == LinkStatus.OK

    def test_skips_template_placeholder(self, tmp_path: Path) -> None:
        src = self._make_source(tmp_path)
        result = check_link(src, 1, "text", "page-{id}.md", tmp_path, False, {})
        assert result.status == LinkStatus.SKIPPED
        assert result.reason == "template placeholder"

    def test_anchor_cache_is_used(self, tmp_path: Path) -> None:
        src = self._make_source(tmp_path)
        target = tmp_path / "other.md"
        target.write_text("# Cached\n", encoding="utf-8")
        cache: dict[Path, set[str]] = {}

        check_link(src, 1, "text", "other.md#cached", tmp_path, False, cache)
        assert target.resolve() in cache

        # Second call should use the cache
        check_link(src, 2, "text2", "other.md#cached", tmp_path, False, cache)


# ===================================================================
# TestScanFile
# ===================================================================

class TestScanFile:
    """Tests for scan_file."""

    def test_inline_links(self, tmp_path: Path) -> None:
        target = tmp_path / "other.md"
        target.write_text("# Other\n", encoding="utf-8")

        source = tmp_path / "source.md"
        source.write_text(
            "See [Other](other.md) for details.\n",
            encoding="utf-8",
        )

        results = scan_file(source, tmp_path, {})
        assert len(results) == 1
        assert results[0].status == LinkStatus.OK
        assert results[0].target == "other.md"

    def test_reference_style_links(self, tmp_path: Path) -> None:
        target = tmp_path / "ref-target.md"
        target.write_text("# Ref Target\n", encoding="utf-8")

        source = tmp_path / "source.md"
        source.write_text(
            "Check out [the reference][ref1] for info.\n\n"
            "[ref1]: ref-target.md\n",
            encoding="utf-8",
        )

        results = scan_file(source, tmp_path, {})
        ok_results = [r for r in results if r.status == LinkStatus.OK]
        assert len(ok_results) >= 1
        targets = {r.target for r in ok_results}
        assert "ref-target.md" in targets

    def test_links_in_fenced_code_blocks_ignored(self, tmp_path: Path) -> None:
        source = tmp_path / "source.md"
        source.write_text(
            "# Title\n\n"
            "```\n"
            "[should be ignored](nonexistent.md)\n"
            "```\n\n"
            "[real link](https://example.com)\n",
            encoding="utf-8",
        )

        results = scan_file(source, tmp_path, {})
        # The fenced link should be ignored, only 'real link' should appear
        broken = [r for r in results if r.status == LinkStatus.BROKEN]
        assert len(broken) == 0

    def test_mixed_link_statuses(self, tmp_path: Path) -> None:
        existing = tmp_path / "exists.md"
        existing.write_text("# Exists\n", encoding="utf-8")

        source = tmp_path / "source.md"
        source.write_text(
            "[good](exists.md)\n"
            "[bad](missing.md)\n"
            "[ext](https://example.com)\n",
            encoding="utf-8",
        )

        results = scan_file(source, tmp_path, {})
        statuses = {r.target: r.status for r in results}
        assert statuses["exists.md"] == LinkStatus.OK
        assert statuses["missing.md"] == LinkStatus.BROKEN
        assert statuses["https://example.com"] == LinkStatus.SKIPPED

    def test_unreadable_file_raises(self, tmp_path: Path) -> None:
        fake = tmp_path / "nonexistent.md"
        with pytest.raises(LinkCheckError):
            scan_file(fake, tmp_path, {})


# ===================================================================
# TestScanAll
# ===================================================================

class TestScanAll:
    """Tests for scan_all and scan_files."""

    def test_scan_all_finds_and_reports(self, tmp_path: Path) -> None:
        target = tmp_path / "target.md"
        target.write_text("# Target\n", encoding="utf-8")

        source = tmp_path / "source.md"
        source.write_text(
            "[ok](target.md)\n[broken](nope.md)\n",
            encoding="utf-8",
        )

        result = scan_all(tmp_path)
        assert result.files_scanned == 2
        assert result.links_ok >= 1
        assert result.links_broken >= 1

    def test_scan_all_extra_skip_dirs(self, tmp_path: Path) -> None:
        (tmp_path / "keep.md").write_text("# Keep\n", encoding="utf-8")
        d = tmp_path / "excluded"
        d.mkdir()
        (d / "skip.md").write_text("# Skip\n", encoding="utf-8")

        result = scan_all(tmp_path, extra_skip_dirs={"excluded"})
        scanned_files = result.files_scanned
        assert scanned_files == 1

    def test_scan_files_with_explicit_list(self, tmp_path: Path) -> None:
        f1 = tmp_path / "one.md"
        f1.write_text("[link](https://example.com)\n", encoding="utf-8")
        f2 = tmp_path / "two.md"
        f2.write_text("[broken](nowhere.md)\n", encoding="utf-8")

        result = scan_files([f1, f2], tmp_path)
        assert result.files_scanned == 2
        assert result.links_skipped >= 1
        assert result.links_broken >= 1

    def test_scan_result_properties(self) -> None:
        sr = ScanResult(
            files_scanned=2,
            results=[
                LinkResult("a.md", 1, "t", "x", LinkStatus.OK),
                LinkResult("a.md", 2, "t", "y", LinkStatus.BROKEN, "file not found"),
                LinkResult("b.md", 1, "t", "z", LinkStatus.SKIPPED, "external"),
            ],
        )
        assert sr.links_checked == 3
        assert sr.links_ok == 1
        assert sr.links_broken == 1
        assert sr.links_skipped == 1

    def test_scan_files_skips_unreadable(self, tmp_path: Path) -> None:
        good = tmp_path / "good.md"
        good.write_text("[ext](https://example.com)\n", encoding="utf-8")
        bad = tmp_path / "bad.md"
        bad.write_text("# Bad\n", encoding="utf-8")

        # Make bad unreadable by deleting it after building the list
        files = [good, bad]
        bad.unlink()

        # scan_files should log a warning and continue, not raise
        result = scan_files(files, tmp_path)
        # good.md was scanned (1 file counted), bad.md was counted but failed
        assert result.files_scanned == 2


# ===================================================================
# TestCLI
# ===================================================================

class TestCLI:
    """Tests for the CLI (build_parser and main)."""

    def test_build_parser_has_expected_arguments(self) -> None:
        parser = build_parser()
        # Parse known flags to verify they exist
        args = parser.parse_args([
            "--no-anchors",
            "--verbose",
            "--json",
            "--no-color",
            "--root", ".",
            "--exclude", "out",
            "--root-relative", "docs/**",
        ])
        assert args.no_anchors is True
        assert args.verbose is True
        assert args.output_json is True
        assert args.no_color is True
        assert args.root == Path(".")
        assert args.exclude == ["out"]
        assert args.root_relative == ["docs/**"]

    def test_build_parser_defaults(self) -> None:
        parser = build_parser()
        args = parser.parse_args([])
        assert args.no_anchors is False
        assert args.verbose is False
        assert args.output_json is False
        assert args.no_color is False
        assert args.root == Path(".")
        assert args.exclude == []
        assert args.root_relative == []

    def test_main_returns_0_no_broken_links(self, tmp_path: Path) -> None:
        f = tmp_path / "ok.md"
        f.write_text("[ext](https://example.com)\n", encoding="utf-8")
        exit_code = main(["--root", str(tmp_path), "--no-color"])
        assert exit_code == 0

    def test_main_returns_1_for_broken_links(self, tmp_path: Path) -> None:
        f = tmp_path / "bad.md"
        f.write_text("[broken](nonexistent.md)\n", encoding="utf-8")
        exit_code = main(["--root", str(tmp_path), "--no-color"])
        assert exit_code == 1

    def test_main_returns_2_for_invalid_root(self, tmp_path: Path) -> None:
        fake_dir = tmp_path / "does_not_exist"
        exit_code = main(["--root", str(fake_dir)])
        assert exit_code == 2

    def test_main_json_output(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        f = tmp_path / "ok.md"
        f.write_text("# Just a heading\n", encoding="utf-8")
        exit_code = main(["--root", str(tmp_path), "--json", "--no-color"])
        assert exit_code == 0
        captured = capsys.readouterr()
        import json
        data = json.loads(captured.out)
        assert data["links_broken"] == 0

    def test_main_with_exclude(self, tmp_path: Path) -> None:
        (tmp_path / "good.md").write_text("# Good\n", encoding="utf-8")
        d = tmp_path / "excluded_dir"
        d.mkdir()
        (d / "bad.md").write_text("[broken](nope.md)\n", encoding="utf-8")

        exit_code = main(["--root", str(tmp_path), "--no-color", "--exclude", "excluded_dir"])
        assert exit_code == 0

    def test_main_verbose(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        f = tmp_path / "ok.md"
        f.write_text("[ext](https://example.com)\n", encoding="utf-8")
        exit_code = main(["--root", str(tmp_path), "--no-color", "--verbose"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "SKIPPED" in captured.out


# ===================================================================
# TestMainModule — subprocess tests for __main__.py
# ===================================================================


class TestMainModule:
    """Tests for running ``python -m dev_tools.md_link_checker``."""

    def test_help_flag_exits_zero(self) -> None:
        """--help should exit 0 and print usage information."""
        result = subprocess.run(
            [sys.executable, "-m", "dev_tools.md_link_checker", "--help"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0
        assert "usage" in result.stdout.lower()

    def test_scan_valid_directory(self, tmp_path: Path) -> None:
        """Running against a directory with a clean markdown file should exit 0."""
        md_file = tmp_path / "readme.md"
        md_file.write_text("# Hello\n", encoding="utf-8")
        result = subprocess.run(
            [
                sys.executable, "-m", "dev_tools.md_link_checker",
                "--root", str(tmp_path), "--no-color",
            ],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0

    def test_invalid_root_exits_nonzero(self, tmp_path: Path) -> None:
        """Running against a non-existent directory should exit with code 2."""
        fake_dir = tmp_path / "does_not_exist"
        result = subprocess.run(
            [
                sys.executable, "-m", "dev_tools.md_link_checker",
                "--root", str(fake_dir),
            ],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 2
