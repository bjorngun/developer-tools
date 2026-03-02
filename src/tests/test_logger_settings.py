import os
import pytest
from unittest.mock import patch
from dev_tools.logger_settings import (
    logger_setup,
    is_script_folders_enabled,
    _get_logger_folder,
)


class TestLoggerSettings:
    @patch("dev_tools.logger_settings.logging.config.dictConfig")
    @patch("dev_tools.logger_settings.Path.exists", return_value=False)
    def test_logger_setup_with_dictConfig(self, _mock_exists, mock_dictConfig):
        logger_setup()
        mock_dictConfig.assert_called_once()

    @patch("dev_tools.logger_settings.logging.config.fileConfig")
    @patch("dev_tools.logger_settings.Path.exists", return_value=True)
    def test_logger_setup_with_fileConfig(self, _mock_exists, mock_fileConfig):
        logger_setup()
        mock_fileConfig.assert_called_once()


class TestIsScriptFoldersEnabled:
    """Tests for is_script_folders_enabled() function."""

    def test_default_is_false(self, monkeypatch):
        """Should return False when env var is not set."""
        monkeypatch.delenv("LOGGER_SCRIPT_FOLDERS", raising=False)
        assert is_script_folders_enabled() is False

    @pytest.mark.parametrize("value", ["true", "True", "TRUE", "1", "t", "yes", "Yes"])
    def test_true_values(self, value, monkeypatch):
        """Should return True for truthy string values."""
        monkeypatch.setenv("LOGGER_SCRIPT_FOLDERS", value)
        assert is_script_folders_enabled() is True

    @pytest.mark.parametrize("value", ["false", "False", "0", "no", "random"])
    def test_false_values(self, value, monkeypatch):
        """Should return False for falsy string values."""
        monkeypatch.setenv("LOGGER_SCRIPT_FOLDERS", value)
        assert is_script_folders_enabled() is False


@pytest.fixture
def _clean_logger_env(monkeypatch):
    """Remove logger-related env vars so each test starts clean."""
    for key in ["LOGGER_PATH", "LOGGER_SCRIPT_FOLDERS", "LOGGER_DAY_SPECIFIC", "SCRIPT_NAME"]:
        monkeypatch.delenv(key, raising=False)


@pytest.mark.usefixtures("_clean_logger_env")
class TestGetLoggerFolder:
    """Tests for _get_logger_folder() function."""

    @patch("dev_tools.logger_settings.datetime")
    def test_default_path_without_script_folders(self, mock_datetime):
        """Should return standard path when script folders disabled."""
        mock_datetime.now.return_value.year = 2026
        mock_datetime.now.return_value.month = 1
        mock_datetime.now.return_value.strftime.return_value = "January"
        mock_datetime.now.return_value.day = 12

        result = _get_logger_folder()
        assert result == "./logs/2026/1.January"

    @patch("dev_tools.logger_settings.datetime")
    def test_script_folder_with_param(self, mock_datetime, monkeypatch):
        """Should include script name in path when enabled and param provided."""
        mock_datetime.now.return_value.year = 2026
        mock_datetime.now.return_value.month = 1
        mock_datetime.now.return_value.strftime.return_value = "January"
        mock_datetime.now.return_value.day = 12

        monkeypatch.setenv("LOGGER_SCRIPT_FOLDERS", "True")

        result = _get_logger_folder(script_name="provisioning")
        assert result == "./logs/provisioning/2026/1.January"

    @patch("dev_tools.logger_settings.datetime")
    def test_script_folder_from_env_var(self, mock_datetime, monkeypatch):
        """Should use SCRIPT_NAME env var when param not provided."""
        mock_datetime.now.return_value.year = 2026
        mock_datetime.now.return_value.month = 1
        mock_datetime.now.return_value.strftime.return_value = "January"
        mock_datetime.now.return_value.day = 12

        monkeypatch.setenv("LOGGER_SCRIPT_FOLDERS", "True")
        monkeypatch.setenv("SCRIPT_NAME", "sync")

        result = _get_logger_folder()
        assert result == "./logs/sync/2026/1.January"

    @patch("dev_tools.logger_settings.datetime")
    def test_script_folder_param_overrides_env(self, mock_datetime, monkeypatch):
        """Script name param should take precedence over env var."""
        mock_datetime.now.return_value.year = 2026
        mock_datetime.now.return_value.month = 1
        mock_datetime.now.return_value.strftime.return_value = "January"
        mock_datetime.now.return_value.day = 12

        monkeypatch.setenv("LOGGER_SCRIPT_FOLDERS", "True")
        monkeypatch.setenv("SCRIPT_NAME", "sync")

        result = _get_logger_folder(script_name="provisioning")
        assert result == "./logs/provisioning/2026/1.January"

    @patch("dev_tools.logger_settings.datetime")
    def test_script_folder_with_day_specific(self, mock_datetime, monkeypatch):
        """Should include day when both script folders and day specific enabled."""
        mock_datetime.now.return_value.year = 2026
        mock_datetime.now.return_value.month = 1
        mock_datetime.now.return_value.strftime.return_value = "January"
        mock_datetime.now.return_value.day = 12

        monkeypatch.setenv("LOGGER_SCRIPT_FOLDERS", "True")
        monkeypatch.setenv("LOGGER_DAY_SPECIFIC", "True")

        result = _get_logger_folder(script_name="provisioning")
        assert result == "./logs/provisioning/2026/1.January/12"

    @patch("dev_tools.logger_settings.datetime")
    def test_no_script_folder_when_disabled(self, mock_datetime, monkeypatch):
        """Should not add script folder even with param when feature disabled."""
        mock_datetime.now.return_value.year = 2026
        mock_datetime.now.return_value.month = 1
        mock_datetime.now.return_value.strftime.return_value = "January"
        mock_datetime.now.return_value.day = 12

        monkeypatch.setenv("LOGGER_SCRIPT_FOLDERS", "False")

        result = _get_logger_folder(script_name="provisioning")
        assert result == "./logs/2026/1.January"

    @patch("dev_tools.logger_settings.datetime")
    def test_custom_logger_path(self, mock_datetime, monkeypatch):
        """Should respect custom LOGGER_PATH."""
        mock_datetime.now.return_value.year = 2026
        mock_datetime.now.return_value.month = 1
        mock_datetime.now.return_value.strftime.return_value = "January"
        mock_datetime.now.return_value.day = 12

        monkeypatch.setenv("LOGGER_PATH", "/var/logs")
        monkeypatch.setenv("LOGGER_SCRIPT_FOLDERS", "True")

        result = _get_logger_folder(script_name="myapp")
        assert result == "/var/logs/myapp/2026/1.January"


class TestLoggerSetupScriptName:
    """Tests for logger_setup() with script_name parameter."""

    @patch("dev_tools.logger_settings.logging.config.dictConfig")
    @patch("dev_tools.logger_settings.Path.exists", return_value=False)
    def test_script_name_sets_env_var(self, _mock_exists, _mock_dictConfig, monkeypatch):
        """Should set SCRIPT_NAME env var when param provided."""
        monkeypatch.delenv("SCRIPT_NAME", raising=False)
        logger_setup(script_name="test_script")
        assert os.environ.get("SCRIPT_NAME") == "test_script"

    @patch("dev_tools.logger_settings.logging.config.dictConfig")
    @patch("dev_tools.logger_settings.Path.exists", return_value=False)
    def test_no_script_name_preserves_env(self, _mock_exists, _mock_dictConfig, monkeypatch):
        """Should not modify SCRIPT_NAME env var when param not provided."""
        monkeypatch.setenv("SCRIPT_NAME", "existing_script")
        logger_setup()
        assert os.environ.get("SCRIPT_NAME") == "existing_script"

    @patch("dev_tools.logger_settings.logging.config.dictConfig")
    @patch("dev_tools.logger_settings.Path.exists", return_value=False)
    def test_backwards_compatible(self, _mock_exists, mock_dictConfig):
        """Should work without any arguments (backwards compatibility)."""
        logger_setup()
        mock_dictConfig.assert_called_once()
