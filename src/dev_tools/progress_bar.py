import logging
import time
from collections.abc import Iterable
from dev_tools.debug_tools import is_debug_on, is_timing_on


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
    Call in a loop to create terminal progress bar
    @params:
        iterable    - Required  : iterable object (Iterable)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        print_end   - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """

    debug = is_debug_on()
    timing = is_timing_on()
    total = len(iterable)
    start_time = time.time()
    logger = logging.getLogger(__name__)
    errors = {}

    def print_progress_bar(iteration: int) -> None:
        if not debug or total == 0:
            return

        percent = f"{100 * (iteration / float(total)):.{decimals}f}"
        filled_length = int(length * iteration // total)
        bar = fill * filled_length + "-" * (length - filled_length)
        time_str = get_timing_str(iteration)

        try:
            print(f"\r{prefix} |{bar}| {percent}% {suffix}{time_str}{'':<10}", end=print_end)
        except UnicodeEncodeError:
            if "UnicodeEncodeError" not in errors:
                errors["UnicodeEncodeError"] = True
                logger.exception("Progress bar is not able to print, DEBUG = %s", debug)
                logging.exception("Progress bar is not able to print, DEBUG = %s", debug)   

    def get_timing_str(iteration: int) -> str:
        if not timing:
            return ""

        et = time.time() - start_time
        et_str = f"Elapsed time: {format_time(et)}"
        eta_str = "Time remaining: N/A"
        if iteration > 0 and et > 0:
            eta_seconds = et / (iteration / float(total)) - et
            eta_str = f"Time remaining: {format_time(eta_seconds)}"

        return f" |--{et_str} - {eta_str}--|"

    def format_time(seconds) -> str:
        minutes = int(seconds // 60)
        seconds = seconds % 60

        hours = int(minutes // 60)
        minutes = minutes % 60

        time_str = ""
        if hours > 0:
            time_str += f"{hours}h "
        if minutes > 0:
            time_str += f"{minutes}m "
        time_str += f"{seconds:.2f}s"
        return time_str

    print_progress_bar(0)
    for i, item in enumerate(iterable):
        yield item
        print_progress_bar(i + 1)
    # Print New Line on Complete
    if debug and total > 0:
        print()
