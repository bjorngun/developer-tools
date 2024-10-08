"""
progress_bar.py

This module provides a progress bar utility for iterables, with support for
debugging and timing estimations.
"""

import logging
import time
from collections.abc import Iterable
from dev_tools.debug_tools import is_debug_on, is_timing_on, human_readable_time


def _get_estimation_time_remaining(
    iteration: int,
    total_iterations: int,
    start_time: float
) -> str:
    """
    Returns a formatted string with elapsed and remaining time.

    Args:
        iteration (int): Current iteration number.
        total_iterations (int): Total number of iterations for the process.
        start_time (float): The time when the process started, in seconds since the epoch.

    Returns:
        str: Formatted string with elapsed time and estimated time remaining.
             If timing is disabled, returns an empty string.
    """
    if not is_timing_on():
        return ""

    et = time.time() - start_time
    et_str = f"Elapsed time: {human_readable_time(et)}"
    eta_str = "Time remaining: N/A"
    if iteration > 0 and et > 0:
        eta_seconds = et / (iteration / float(total_iterations)) - et
        eta_str = f"Time remaining: {human_readable_time(eta_seconds)}"

    return f" |--{et_str} - {eta_str}--|"

def progress_bar(
    iterable: Iterable,
    decimals: int = 1,
    length: int = 50,
    **kwargs: dict,
) -> Iterable:
    """
    Displays a terminal progress bar for an iterable.

    Args:
        iterable (Iterable): Required. Iterable object to track progress.
        decimals (int): Optional. Number of decimals in percent complete. Default is 1.
        length (int): Optional. Character length of the progress bar. Default is 50.
        **kwargs (dict): Additional optional arguments:
            - prefix (str): Prefix string for the progress bar. Default is "".
            - suffix (str): Suffix string for the progress bar. Default is "".
            - fill (str): Bar fill character. Default is "█".
            - print_end (str): End character (e.g., "\r", "\r\n"). Default is "\r".

    Yields:
        Iterable: Items from the provided iterable, with progress displayed.
    """

    total = len(iterable)
    start_time = time.time()
    logger = logging.getLogger(__name__)
    prefix = kwargs.get('prefix', '')
    suffix = kwargs.get('suffix', '')
    fill = kwargs.get('fill', '█')
    print_end = kwargs.get('print_end', '\r')
    errors = {}

    def print_progress_bar(iteration: int) -> None:
        """
        Prints the progress bar to the terminal.

        Args:
            iteration (int): Current iteration number.
        """
        if not is_debug_on() or total == 0:
            return

        percent = f"{100 * (iteration / float(total)):.{decimals}f}"
        filled_length = int(length * iteration // total)
        bar_str = fill * filled_length + "-" * (length - filled_length)
        time_str = _get_estimation_time_remaining(iteration, total, start_time)

        try:
            print(
                f"\r{prefix} |{bar_str}| {percent}% {suffix}{time_str}{'':<10}",
                end=print_end,
            )
        except UnicodeEncodeError:
            if "UnicodeEncodeError" not in errors:
                errors["UnicodeEncodeError"] = True
                logger.exception(
                    "Progress bar is not able to print, DEBUG = %s", is_debug_on()
                )

    print_progress_bar(0)
    for i, item in enumerate(iterable):
        yield item
        print_progress_bar(i + 1)
    # Print New Line on Complete
    if is_debug_on() and total > 0:
        print()
