import os
import unittest
from unittest.mock import patch
from dev_tools.logger_settings import (
    logger_setup,
    is_script_folders_enabled,
    _get_logger_folder,
)


class TestLoggerSettings(unittest.TestCase):
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


class TestIsScriptFoldersEnabled(unittest.TestCase):
    """Tests for is_script_folders_enabled() function."""

    def tearDown(self):
        # Clean up environment variable after each test
        if "LOGGER_SCRIPT_FOLDERS" in os.environ:
            del os.environ["LOGGER_SCRIPT_FOLDERS"]

    def test_default_is_false(self):
        """Should return False when env var is not set."""
        self.assertFalse(is_script_folders_enabled())

    def test_true_values(self):
        """Should return True for truthy string values."""
        for value in ["true", "True", "TRUE", "1", "t", "yes", "Yes"]:
            with self.subTest(value=value):
                os.environ["LOGGER_SCRIPT_FOLDERS"] = value
                self.assertTrue(is_script_folders_enabled())

    def test_false_values(self):
        """Should return False for falsy string values."""
        for value in ["false", "False", "0", "no", "random"]:
            with self.subTest(value=value):
                os.environ["LOGGER_SCRIPT_FOLDERS"] = value
                self.assertFalse(is_script_folders_enabled())


class TestGetLoggerFolder(unittest.TestCase):
    """Tests for _get_logger_folder() function."""

    def setUp(self):
        self.env_backup = {}
        for key in ["LOGGER_PATH", "LOGGER_SCRIPT_FOLDERS", "LOGGER_DAY_SPECIFIC", "SCRIPT_NAME"]:
            self.env_backup[key] = os.environ.get(key)

    def tearDown(self):
        # Restore environment variables
        for key, value in self.env_backup.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    @patch("dev_tools.logger_settings.datetime")
    def test_default_path_without_script_folders(self, mock_datetime):
        """Should return standard path when script folders disabled."""
        mock_datetime.now.return_value.year = 2026
        mock_datetime.now.return_value.month = 1
        mock_datetime.now.return_value.strftime.return_value = "January"
        mock_datetime.now.return_value.day = 12

        os.environ.pop("LOGGER_SCRIPT_FOLDERS", None)
        os.environ.pop("LOGGER_DAY_SPECIFIC", None)

        result = _get_logger_folder()
        self.assertEqual(result, "./logs/2026/1.January")

    @patch("dev_tools.logger_settings.datetime")
    def test_script_folder_with_param(self, mock_datetime):
        """Should include script name in path when enabled and param provided."""
        mock_datetime.now.return_value.year = 2026
        mock_datetime.now.return_value.month = 1
        mock_datetime.now.return_value.strftime.return_value = "January"
        mock_datetime.now.return_value.day = 12

        os.environ["LOGGER_SCRIPT_FOLDERS"] = "True"
        os.environ.pop("LOGGER_DAY_SPECIFIC", None)

        result = _get_logger_folder(script_name="provisioning")
        self.assertEqual(result, "./logs/provisioning/2026/1.January")

    @patch("dev_tools.logger_settings.datetime")
    def test_script_folder_from_env_var(self, mock_datetime):
        """Should use SCRIPT_NAME env var when param not provided."""
        mock_datetime.now.return_value.year = 2026
        mock_datetime.now.return_value.month = 1
        mock_datetime.now.return_value.strftime.return_value = "January"
        mock_datetime.now.return_value.day = 12

        os.environ["LOGGER_SCRIPT_FOLDERS"] = "True"
        os.environ["SCRIPT_NAME"] = "sync"
        os.environ.pop("LOGGER_DAY_SPECIFIC", None)

        result = _get_logger_folder()
        self.assertEqual(result, "./logs/sync/2026/1.January")

    @patch("dev_tools.logger_settings.datetime")
    def test_script_folder_param_overrides_env(self, mock_datetime):
        """Script name param should take precedence over env var."""
        mock_datetime.now.return_value.year = 2026
        mock_datetime.now.return_value.month = 1
        mock_datetime.now.return_value.strftime.return_value = "January"
        mock_datetime.now.return_value.day = 12

        os.environ["LOGGER_SCRIPT_FOLDERS"] = "True"
        os.environ["SCRIPT_NAME"] = "sync"
        os.environ.pop("LOGGER_DAY_SPECIFIC", None)

        result = _get_logger_folder(script_name="provisioning")
        self.assertEqual(result, "./logs/provisioning/2026/1.January")

    @patch("dev_tools.logger_settings.datetime")
    def test_script_folder_with_day_specific(self, mock_datetime):
        """Should include day when both script folders and day specific enabled."""
        mock_datetime.now.return_value.year = 2026
        mock_datetime.now.return_value.month = 1
        mock_datetime.now.return_value.strftime.return_value = "January"
        mock_datetime.now.return_value.day = 12

        os.environ["LOGGER_SCRIPT_FOLDERS"] = "True"
        os.environ["LOGGER_DAY_SPECIFIC"] = "True"

        result = _get_logger_folder(script_name="provisioning")
        self.assertEqual(result, "./logs/provisioning/2026/1.January/12")

    @patch("dev_tools.logger_settings.datetime")
    def test_no_script_folder_when_disabled(self, mock_datetime):
        """Should not add script folder even with param when feature disabled."""
        mock_datetime.now.return_value.year = 2026
        mock_datetime.now.return_value.month = 1
        mock_datetime.now.return_value.strftime.return_value = "January"
        mock_datetime.now.return_value.day = 12

        os.environ["LOGGER_SCRIPT_FOLDERS"] = "False"
        os.environ.pop("LOGGER_DAY_SPECIFIC", None)

        result = _get_logger_folder(script_name="provisioning")
        self.assertEqual(result, "./logs/2026/1.January")

    @patch("dev_tools.logger_settings.datetime")
    def test_custom_logger_path(self, mock_datetime):
        """Should respect custom LOGGER_PATH."""
        mock_datetime.now.return_value.year = 2026
        mock_datetime.now.return_value.month = 1
        mock_datetime.now.return_value.strftime.return_value = "January"
        mock_datetime.now.return_value.day = 12

        os.environ["LOGGER_PATH"] = "/var/logs"
        os.environ["LOGGER_SCRIPT_FOLDERS"] = "True"
        os.environ.pop("LOGGER_DAY_SPECIFIC", None)

        result = _get_logger_folder(script_name="myapp")
        self.assertEqual(result, "/var/logs/myapp/2026/1.January")


class TestLoggerSetupScriptName(unittest.TestCase):
    """Tests for logger_setup() with script_name parameter."""

    def setUp(self):
        self.script_name_backup = os.environ.get("SCRIPT_NAME")

    def tearDown(self):
        if self.script_name_backup is None:
            os.environ.pop("SCRIPT_NAME", None)
        else:
            os.environ["SCRIPT_NAME"] = self.script_name_backup

    @patch("dev_tools.logger_settings.logging.config.dictConfig")
    @patch("dev_tools.logger_settings.Path.exists", return_value=False)
    def test_script_name_sets_env_var(self, _mock_exists, _mock_dictConfig):
        """Should set SCRIPT_NAME env var when param provided."""
        os.environ.pop("SCRIPT_NAME", None)
        logger_setup(script_name="test_script")
        self.assertEqual(os.environ.get("SCRIPT_NAME"), "test_script")

    @patch("dev_tools.logger_settings.logging.config.dictConfig")
    @patch("dev_tools.logger_settings.Path.exists", return_value=False)
    def test_no_script_name_preserves_env(self, _mock_exists, _mock_dictConfig):
        """Should not modify SCRIPT_NAME env var when param not provided."""
        os.environ["SCRIPT_NAME"] = "existing_script"
        logger_setup()
        self.assertEqual(os.environ.get("SCRIPT_NAME"), "existing_script")

    @patch("dev_tools.logger_settings.logging.config.dictConfig")
    @patch("dev_tools.logger_settings.Path.exists", return_value=False)
    def test_backwards_compatible(self, _mock_exists, mock_dictConfig):
        """Should work without any arguments (backwards compatibility)."""
        logger_setup()
        mock_dictConfig.assert_called_once()


if __name__ == "__main__":
    unittest.main()
