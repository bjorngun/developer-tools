import logging
import time
from collections.abc import Iterable
from dev_tools.debug_tools import is_debug_on, is_timing_on, human_readable_time


def progress_bar(
    iterable: Iterable,
    prefix: str = "",
    suffix: str = "",
    decimals: int = 1,
    length: int = 50,
    fill: str = "█",
    print_end: str = "\r",
) -> Iterable:
    """
    Displays a terminal progress bar for an iterable.

    Args:
        iterable (Iterable): Required. Iterable object to track progress.
        prefix (str): Optional. Prefix string for the progress bar. Default is "".
        suffix (str): Optional. Suffix string for the progress bar. Default is "".
        decimals (int): Optional. Number of decimals in percent complete. Default is 1.
        length (int): Optional. Character length of the progress bar. Default is 50.
        fill (str): Optional. Bar fill character. Default is "█".
        print_end (str): Optional. End character (e.g., "\r", "\r\n"). Default is "\r".

    Yields:
        Iterable: Items from the provided iterable, with progress displayed.
    """

    debug = is_debug_on()
    timing = is_timing_on()
    total = len(iterable)
    start_time = time.time()
    logger = logging.getLogger(__name__)
    errors = {}

    def print_progress_bar(iteration: int) -> None:
        """
        Prints the progress bar to the terminal.

        Args:
            iteration (int): Current iteration number.
        """
        if not debug or total == 0:
            return

        percent = f"{100 * (iteration / float(total)):.{decimals}f}"
        filled_length = int(length * iteration // total)
        bar = fill * filled_length + "-" * (length - filled_length)
        time_str = get_estimations(iteration)

        try:
            print(f"\r{prefix} |{bar}| {percent}% {suffix}{time_str}{'':<10}", end=print_end)
        except UnicodeEncodeError:
            if "UnicodeEncodeError" not in errors:
                errors["UnicodeEncodeError"] = True
                logger.exception("Progress bar is not able to print, DEBUG = %s", debug)
                logging.exception("Progress bar is not able to print, DEBUG = %s", debug)   

    def get_estimations(iteration: int) -> str:
        """
        Returns a formatted string with elapsed and remaining time.

        Args:
            iteration (int): Current iteration number.

        Returns:
            str: Formatted string with elapsed and remaining time.
        """
        if not timing:
            return ""

        et = time.time() - start_time
        et_str = f"Elapsed time: {human_readable_time(et)}"
        eta_str = "Time remaining: N/A"
        if iteration > 0 and et > 0:
            eta_seconds = et / (iteration / float(total)) - et
            eta_str = f"Time remaining: {human_readable_time(eta_seconds)}"

        return f" |--{et_str} - {eta_str}--|"

    print_progress_bar(0)
    for i, item in enumerate(iterable):
        yield item
        print_progress_bar(i + 1)
    # Print New Line on Complete
    if debug and total > 0:
        print()
