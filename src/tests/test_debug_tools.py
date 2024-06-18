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
    def test_logger_setup_with_dictConfig(self, _mock_exists, mock_dictConfig):
        logger_setup()
        mock_dictConfig.assert_called_once()

    @patch("dev_tools.debug_tools.logging.config.fileConfig")
    @patch("dev_tools.debug_tools.Path.exists", return_value=True)
    def test_logger_setup_with_fileConfig(self, _mock_exists, mock_fileConfig):
        logger_setup()
        mock_fileConfig.assert_called_once()

    def test_human_readable_time(self):
        self.assertEqual(
            human_readable_time(12345678.251),
            "142 days 21h 21m 18.251s"
        )

    def test_zero_seconds(self):
        self.assertEqual(human_readable_time(0), "0.000s")

    def test_seconds_only(self):
        self.assertEqual(human_readable_time(5), "5.000s")
        self.assertEqual(human_readable_time(59), "59.000s")

    def test_minutes_and_seconds(self):
        self.assertEqual(human_readable_time(65), "1m 5.000s")
        self.assertEqual(human_readable_time(3605), "1h 5.000s")

    def test_hours_minutes_and_seconds(self):
        self.assertEqual(human_readable_time(3665), "1h 1m 5.000s")
        self.assertEqual(human_readable_time(86399), "23h 59m 59.000s")

    def test_days_hours_minutes_and_seconds(self):
        self.assertEqual(human_readable_time(90061), "1 day 1h 1m 1.000s")
        self.assertEqual(human_readable_time(172800), "2 days")
        self.assertEqual(human_readable_time(28771200), "333 days")
        self.assertEqual(human_readable_time(28783989), "333 days 3h 33m 9.000s")

    def test_years_days_hours_minutes_and_seconds(self):
        self.assertEqual(human_readable_time(31536000), "1 year")
        self.assertEqual(human_readable_time(31536061), "1 year 1m 1.000s")
        self.assertEqual(human_readable_time(63115200), "2 years")
        self.assertEqual(human_readable_time(63115261), "2 years 1m 1.000s")
        self.assertEqual(human_readable_time(63122461), "2 years 2h 1m 1.000s")

    def test_multiple_units(self):
        self.assertEqual(human_readable_time(123456789), "3 years 333 days 3h 33m 9.000s")


if __name__ == "__main__":
    unittest.main()
