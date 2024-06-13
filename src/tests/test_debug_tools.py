import unittest
import os
from unittest.mock import patch
from dev_tools.debug_tools import (
    is_debug_on,
    is_timing_on,
    logger_setup,
    human_readable_time,
)


class TestDebugTools(unittest.TestCase):
    @patch.dict(os.environ, {"DEBUG": "true", "TIMING": "true"})
    def test_is_debug_on(self):
        self.assertTrue(is_debug_on())

    @patch.dict(os.environ, {"DEBUG": "false", "TIMING": "true"})
    def test_is_timing_on(self):
        self.assertTrue(is_timing_on())

    @patch("dev_tools.debug_tools.logging.config.dictConfig")
    @patch("dev_tools.debug_tools.Path.exists", return_value=False)
    def test_logger_setup_with_dictConfig(self, mock_exists, mock_dictConfig):
        logger_setup()
        mock_dictConfig.assert_called_once()

    @patch("dev_tools.debug_tools.logging.config.fileConfig")
    @patch("dev_tools.debug_tools.Path.exists", return_value=True)
    def test_logger_setup_with_fileConfig(self, mock_exists, mock_fileConfig):
        logger_setup()
        mock_fileConfig.assert_called_once()

    def test_human_readable_time(self):
        self.assertEqual(
            human_readable_time(12345678.251),
            "142 days 21h 21m 18.251s"
        )


if __name__ == "__main__":
    unittest.main()
