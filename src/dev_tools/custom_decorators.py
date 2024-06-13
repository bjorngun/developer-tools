import time
from typing import Any, Callable
from functools import wraps

from dev_tools.debug_tools import is_timing_on


def timing_decorator(func: Callable) -> Callable:
    """
    Decorator that prints and optionally logs the elapsed time of the wrapped function.

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

        # Print elapsed time
        print(f"Elapsed time for {func.__name__}: {elapsed_time:.2f} seconds")

        # Check if timing is enabled and log if applicable
        if is_timing_on() and args and hasattr(args[0], 'logger'):
            logger = getattr(args[0], 'logger')
            logger.info(f"Elapsed time for {func.__name__}: {elapsed_time:.2f} seconds")

        return result
    return wrapper
