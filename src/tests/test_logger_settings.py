import unittest
from unittest.mock import patch
from dev_tools.logger_settings import logger_setup


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


if __name__ == "__main__":
    unittest.main()
