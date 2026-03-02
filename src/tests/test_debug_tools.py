import os
import pytest
from unittest.mock import patch
from dev_tools.debug_tools import (
    is_debug_on,
    is_timing_on,
    human_readable_time,
)


class TestDebugTools:
    @patch.dict(os.environ, {"DEBUG": "true", "TIMING": "true"})
    def test_is_debug_on(self):
        assert is_debug_on() is True

    @patch.dict(os.environ, {"DEBUG": "false", "TIMING": "true"})
    def test_is_timing_on(self):
        assert is_timing_on() is True

    def test_human_readable_time(self):
        assert human_readable_time(12345678.251) == "142 days 21h 21m 18.251s"

    def test_zero_seconds(self):
        assert human_readable_time(0) == "0.000s"

    def test_seconds_only(self):
        assert human_readable_time(5) == "5.000s"
        assert human_readable_time(59) == "59.000s"

    def test_minutes_and_seconds(self):
        assert human_readable_time(65) == "1m 5.000s"
        assert human_readable_time(3605) == "1h 5.000s"

    def test_hours_minutes_and_seconds(self):
        assert human_readable_time(3665) == "1h 1m 5.000s"
        assert human_readable_time(86399) == "23h 59m 59.000s"

    def test_days_hours_minutes_and_seconds(self):
        assert human_readable_time(90061) == "1 day 1h 1m 1.000s"
        assert human_readable_time(172800) == "2 days"
        assert human_readable_time(28771200) == "333 days"
        assert human_readable_time(28783989) == "333 days 3h 33m 9.000s"

    def test_years_days_hours_minutes_and_seconds(self):
        assert human_readable_time(31536000) == "1 year"
        assert human_readable_time(31536061) == "1 year 1m 1.000s"
        assert human_readable_time(63115200) == "2 years"
        assert human_readable_time(63115261) == "2 years 1m 1.000s"
        assert human_readable_time(63122461) == "2 years 2h 1m 1.000s"

    def test_multiple_units(self):
        assert (
            human_readable_time(123456789) == "3 years 333 days 3h 33m 9.000s"
        )
