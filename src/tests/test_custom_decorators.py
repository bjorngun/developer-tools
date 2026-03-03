from unittest.mock import patch

from dev_tools.custom_decorators import timing_decorator


def test_timing_decorator_no_output_when_timing_off():
    """When TIMING is not enabled, timing_decorator should not print anything."""

    @timing_decorator
    def sample_function(x, y):
        return x + y

    with patch("dev_tools.custom_decorators.is_timing_on", return_value=False):
        with patch("builtins.print") as mock_print:
            result = sample_function(1, 2)
            assert result == 3
            mock_print.assert_not_called()


def test_timing_decorator_prints_when_timing_on():
    """When TIMING is enabled, timing_decorator should print elapsed time."""

    @timing_decorator
    def sample_function(x, y):
        return x + y

    with patch("dev_tools.custom_decorators.is_timing_on", return_value=True):
        with patch("builtins.print") as mock_print:
            result = sample_function(1, 2)
            assert result == 3
            mock_print.assert_called_once()
            output = mock_print.call_args[0][0]
            assert "Elapsed time for sample_function" in output


def test_timing_decorator_logs_when_logger_available():
    """When TIMING is on and first arg has a logger, it should also log."""

    class FakeObj:
        """Fake object with a logger attribute."""
        def __init__(self):
            self.logger = type("Logger", (), {"info": lambda self, msg: None})()

    @timing_decorator
    def method(obj, x):
        return x

    fake = FakeObj()
    with patch("dev_tools.custom_decorators.is_timing_on", return_value=True):
        with patch.object(fake.logger, "info") as mock_log:
            result = method(fake, 42)
            assert result == 42
            mock_log.assert_called_once()
            assert "Elapsed time for method" in mock_log.call_args[0][0]
