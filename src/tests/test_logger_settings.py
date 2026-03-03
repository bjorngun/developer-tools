import logging
import os
import pytest
from unittest.mock import patch
from dev_tools.logger_settings import (
    logger_setup,
    is_script_folders_enabled,
    is_logs_sorted_by_days,
    log_exit_code,
    _get_logger_folder,
    _default_logging_config,
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
        mock_datetime.now.return_value.day = 12

        result = _get_logger_folder()
        assert result == "./logs/2026/01"

    @patch("dev_tools.logger_settings.datetime")
    def test_script_folder_with_param(self, mock_datetime, monkeypatch):
        """Should include script name in path when enabled and param provided."""
        mock_datetime.now.return_value.year = 2026
        mock_datetime.now.return_value.month = 1
        mock_datetime.now.return_value.day = 12

        monkeypatch.setenv("LOGGER_SCRIPT_FOLDERS", "True")

        result = _get_logger_folder(script_name="provisioning")
        assert result == "./logs/provisioning/2026/01"

    @patch("dev_tools.logger_settings.datetime")
    def test_script_folder_from_env_var(self, mock_datetime, monkeypatch):
        """Should use SCRIPT_NAME env var when param not provided."""
        mock_datetime.now.return_value.year = 2026
        mock_datetime.now.return_value.month = 1
        mock_datetime.now.return_value.day = 12

        monkeypatch.setenv("LOGGER_SCRIPT_FOLDERS", "True")
        monkeypatch.setenv("SCRIPT_NAME", "sync")

        result = _get_logger_folder()
        assert result == "./logs/sync/2026/01"

    @patch("dev_tools.logger_settings.datetime")
    def test_script_folder_param_overrides_env(self, mock_datetime, monkeypatch):
        """Script name param should take precedence over env var."""
        mock_datetime.now.return_value.year = 2026
        mock_datetime.now.return_value.month = 1
        mock_datetime.now.return_value.day = 12

        monkeypatch.setenv("LOGGER_SCRIPT_FOLDERS", "True")
        monkeypatch.setenv("SCRIPT_NAME", "sync")

        result = _get_logger_folder(script_name="provisioning")
        assert result == "./logs/provisioning/2026/01"

    @patch("dev_tools.logger_settings.datetime")
    def test_script_folder_with_day_specific(self, mock_datetime, monkeypatch):
        """Should include day when both script folders and day specific enabled."""
        mock_datetime.now.return_value.year = 2026
        mock_datetime.now.return_value.month = 1
        mock_datetime.now.return_value.day = 12

        monkeypatch.setenv("LOGGER_SCRIPT_FOLDERS", "True")
        monkeypatch.setenv("LOGGER_DAY_SPECIFIC", "True")

        result = _get_logger_folder(script_name="provisioning")
        assert result == "./logs/provisioning/2026/01/12"

    @patch("dev_tools.logger_settings.datetime")
    def test_no_script_folder_when_disabled(self, mock_datetime, monkeypatch):
        """Should not add script folder even with param when feature disabled."""
        mock_datetime.now.return_value.year = 2026
        mock_datetime.now.return_value.month = 1
        mock_datetime.now.return_value.day = 12

        monkeypatch.setenv("LOGGER_SCRIPT_FOLDERS", "False")

        result = _get_logger_folder(script_name="provisioning")
        assert result == "./logs/2026/01"

    @patch("dev_tools.logger_settings.datetime")
    def test_custom_logger_path(self, mock_datetime, monkeypatch):
        """Should respect custom LOGGER_PATH."""
        mock_datetime.now.return_value.year = 2026
        mock_datetime.now.return_value.month = 1
        mock_datetime.now.return_value.day = 12

        monkeypatch.setenv("LOGGER_PATH", "/var/logs")
        monkeypatch.setenv("LOGGER_SCRIPT_FOLDERS", "True")

        result = _get_logger_folder(script_name="myapp")
        assert result == "/var/logs/myapp/2026/01"


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


# ===================================================================
# TestIsLogsSortedByDays
# ===================================================================


class TestIsLogsSortedByDays:
    """Tests for is_logs_sorted_by_days() function."""

    def test_default_is_false(self, monkeypatch):
        """Should return False when LOGGER_DAY_SPECIFIC is not set."""
        monkeypatch.delenv("LOGGER_DAY_SPECIFIC", raising=False)
        assert is_logs_sorted_by_days() is False

    @pytest.mark.parametrize("value", ["true", "True", "TRUE", "1", "t", "yes", "Yes"])
    def test_true_values(self, value, monkeypatch):
        """Should return True for truthy string values."""
        monkeypatch.setenv("LOGGER_DAY_SPECIFIC", value)
        assert is_logs_sorted_by_days() is True

    @pytest.mark.parametrize("value", ["false", "False", "0", "no", "random"])
    def test_false_values(self, value, monkeypatch):
        """Should return False for falsy or unrecognised string values."""
        monkeypatch.setenv("LOGGER_DAY_SPECIFIC", value)
        assert is_logs_sorted_by_days() is False


# ===================================================================
# TestLogExitCode
# ===================================================================


class TestLogExitCode:
    """Tests for log_exit_code() function."""

    def test_logs_zero_when_no_exception(self, caplog):
        """Should log exit code 0 when no active exception."""
        with caplog.at_level(logging.INFO, logger="dev_tools.logger_settings"):
            log_exit_code()
        assert "Exit code: 0" in caplog.text

    def test_logs_one_when_exception_active(self, caplog):
        """Should log exit code 1 when an unhandled exception is active."""
        try:
            raise ValueError("test error")
        except ValueError:
            # sys.exc_info() is non-None inside the except block
            with caplog.at_level(logging.INFO, logger="dev_tools.logger_settings"):
                log_exit_code()
        assert "Exit code: 1" in caplog.text


# ===================================================================
# TestLoggerSetupErrorPaths
# ===================================================================


class TestLoggerSetupErrorPaths:
    """Tests for error handling branches in logger_setup()."""

    @patch("dev_tools.logger_settings.Path.mkdir", side_effect=OSError("permission denied"))
    def test_mkdir_failure_prints_and_raises(self, _mock_mkdir, capsys):
        """Should print to stderr and re-raise when log directory creation fails."""
        with pytest.raises(OSError, match="permission denied"):
            logger_setup()
        captured = capsys.readouterr()
        assert "Error creating log directory" in captured.err

    @patch("dev_tools.logger_settings.logging.config.fileConfig",
           side_effect=Exception("bad config"))
    @patch("dev_tools.logger_settings.Path.exists", return_value=True)
    def test_fileconfig_failure_prints_and_raises(self, _mock_exists, _mock_fc, capsys):
        """Should print to stderr and re-raise when fileConfig fails."""
        with pytest.raises(Exception, match="bad config"):
            logger_setup()
        captured = capsys.readouterr()
        assert "Error setting up logging configuration" in captured.err


# ===================================================================
# TestLoggerSetupDebugMode
# ===================================================================


class TestLoggerSetupDebugMode:
    """Tests for debug-mode branch in logger_setup()."""

    @patch("dev_tools.logger_settings.logging.config.dictConfig")
    @patch("dev_tools.logger_settings.Path.exists", return_value=False)
    @patch("dev_tools.logger_settings.is_debug_on", return_value=True)
    def test_debug_uses_dev_conf_path(self, _mock_debug, _mock_exists, _mock_dc, monkeypatch):
        """When debug is on, should attempt to load LOGGER_CONF_DEV_PATH."""
        monkeypatch.setenv("LOGGER_CONF_DEV_PATH", "my_dev_logging.conf")
        # The conf file doesn't exist (mocked), so dictConfig is used.
        # We just verify the function completes without error in debug mode.
        logger_setup()
        _mock_dc.assert_called_once()

    @patch("dev_tools.logger_settings.logging.config.fileConfig")
    @patch("dev_tools.logger_settings.Path.exists", return_value=True)
    @patch("dev_tools.logger_settings.is_debug_on", return_value=True)
    def test_debug_fileconfig_path(self, _mock_debug, _mock_exists, mock_fc, monkeypatch):
        """When debug is on and config exists, should use fileConfig with dev path."""
        monkeypatch.setenv("LOGGER_CONF_DEV_PATH", "my_dev_logging.conf")
        logger_setup()
        mock_fc.assert_called_once()


# ===================================================================
# TestDefaultLoggingConfig
# ===================================================================


class TestDefaultLoggingConfig:
    """Tests for _default_logging_config() return value."""

    def test_returns_valid_dict_config(self):
        """Should return a dict with version, formatters, handlers, root keys."""
        config = _default_logging_config("/tmp/test.log")
        assert config["version"] == 1
        assert "formatters" in config
        assert "handlers" in config
        assert "root" in config
        assert config["handlers"]["file"]["filename"] == "/tmp/test.log"

    @patch("dev_tools.logger_settings.is_debug_on", return_value=True)
    def test_debug_mode_levels(self, _mock_debug):
        """In debug mode, handler levels should be lower (DEBUG/INFO)."""
        config = _default_logging_config("/tmp/test.log")
        assert config["handlers"]["screen"]["level"] == "INFO"
        assert config["handlers"]["file"]["level"] == "DEBUG"
        assert config["root"]["level"] == "DEBUG"

    @patch("dev_tools.logger_settings.is_debug_on", return_value=False)
    def test_non_debug_mode_levels(self, _mock_debug):
        """In non-debug mode, handler levels should be higher (WARNING/INFO)."""
        config = _default_logging_config("/tmp/test.log")
        assert config["handlers"]["screen"]["level"] == "WARNING"
        assert config["handlers"]["file"]["level"] == "INFO"
        assert config["root"]["level"] == "INFO"
