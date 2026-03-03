"""Tests for the dev-tools CLI help module."""

import sys
from importlib.metadata import version as pkg_version
from io import StringIO

import pytest

from dev_tools.cli_help import main, _build_parser


class TestBuildParser:
    """Tests for the argument parser construction."""

    def test_parser_prog_name(self):
        """Parser prog should be 'dev-tools'."""
        parser = _build_parser()
        assert parser.prog == "dev-tools"

    def test_parser_has_section_flags(self):
        """All section flags should be recognised without error."""
        parser = _build_parser()
        for flag in ("--api", "--env", "--cli", "--examples", "--all"):
            args = parser.parse_args([flag])
            assert getattr(args, flag.lstrip("-").replace("-", "_"))


class TestMainOutput:
    """Tests for the main() entry point output."""

    @staticmethod
    def _capture(argv: list[str] | None = None) -> str:
        """Run main() and return captured stdout."""
        buf = StringIO()
        old_stdout = sys.stdout
        sys.stdout = buf
        try:
            main(argv)
        finally:
            sys.stdout = old_stdout
        return buf.getvalue()

    def test_no_args_shows_overview(self):
        """Running with no args should print the overview section."""
        output = self._capture([])
        assert "bosos-dev-tools" in output
        assert "Quick start" in output

    def test_no_args_shows_tip(self):
        """Running with no args should print the tip about flags."""
        output = self._capture([])
        assert "--all" in output
        assert "Tip:" in output

    def test_api_flag(self):
        """--api should show the public API reference."""
        output = self._capture(["--api"])
        assert "logger_setup" in output
        assert "timing_decorator" in output
        assert "progress_bar" in output
        assert "scan_all" in output
        assert "CodeMapGenerator" in output

    def test_env_flag(self):
        """--env should show environment variables."""
        output = self._capture(["--env"])
        assert "DEBUG" in output
        assert "TIMING" in output
        assert "LOGGER_PATH" in output
        assert "LOGGER_DAY_SPECIFIC" in output

    def test_cli_flag(self):
        """--cli should show CLI tools."""
        output = self._capture(["--cli"])
        assert "md-link-checker" in output
        assert "codemap-generator" in output
        assert "dev-tools" in output

    def test_examples_flag(self):
        """--examples should show usage examples."""
        output = self._capture(["--examples"])
        assert "from dev_tools import" in output
        assert "@timing_decorator" in output
        assert "progress_bar" in output

    def test_all_flag(self):
        """--all should include every section."""
        output = self._capture(["--all"])
        # Overview
        assert "Quick start" in output
        # API
        assert "logger_setup" in output
        # Env
        assert "LOGGER_PATH" in output
        # CLI
        assert "md-link-checker" in output
        # Examples
        assert "@timing_decorator" in output
        # Should NOT contain the tip line
        assert "Tip:" not in output

    def test_version_flag(self, capsys):
        """--version should print version and exit."""
        with pytest.raises(SystemExit) as exc_info:
            main(["--version"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert pkg_version("bosos-dev-tools") in captured.out

    def test_multiple_flags(self):
        """Multiple section flags can be combined."""
        output = self._capture(["--api", "--env"])
        assert "logger_setup" in output
        assert "LOGGER_PATH" in output
        # Should not contain examples section
        assert "@timing_decorator" not in output
