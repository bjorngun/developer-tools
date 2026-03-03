"""
custom_decorators.py

This module provides a timing decorator to measure and optionally log the execution time of
functions.
"""

import time
from typing import Any, Callable
from functools import wraps

from dev_tools.debug_tools import is_timing_on


def timing_decorator(func: Callable) -> Callable:
    """
    Decorator that measures execution time of the wrapped function.

    When the ``TIMING`` environment variable is enabled (via ``is_timing_on()``),
    prints the elapsed time and optionally logs it if the first positional
    argument has a ``logger`` attribute.

    Args:
        func (Callable): The function to be decorated.

    Returns:
        Callable: The wrapped function with timing functionality.
    """

    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time

        # Only output timing information when timing is explicitly enabled
        if is_timing_on():
            print(f"Elapsed time for {func.__name__}: {elapsed_time:.2f} seconds")

            # Log if the first argument has a logger attribute
            if args and hasattr(args[0], "logger"):
                logger = getattr(args[0], "logger")
                logger.info(f"Elapsed time for {func.__name__}: {elapsed_time:.2f} seconds")

        return result

    return wrapper
