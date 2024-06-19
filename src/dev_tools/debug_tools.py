"""
debug_tools.py

This module provides utilities for debugging and timing, including functions to check if debugging
or timing is enabled
and to log exceptions.
"""

import atexit
from datetime import datetime
import logging
import logging.config
import os
import sys
from pathlib import Path
from enum import Enum
from dotenv import load_dotenv


from .custom_handlers import LogDBHandler


def is_debug_on() -> bool:
    """Check if debug mode is enabled via environment variable."""
    return os.getenv("DEBUG", "False").lower() in ["true", "1", "t", "yes"]


def is_timing_on() -> bool:
    """Check if timing mode is enabled via environment variable."""
    return os.getenv("TIMING", "False").lower() in ["true", "1", "t", "yes"]


def is_database_logging_on() -> bool:
    """Check if database logging is enabled via environment variable."""
    return os.getenv("LOGGER_DATABASE", "False").lower() in ["true", "1", "t", "yes"]


def log_exit_code() -> None:
    """Log the exit code of the script."""
    logger = logging.getLogger(__name__)
    exit_code = 0 if sys.exc_info() == (None, None, None) else 1
    logger.info("Exit code: %s", exit_code)


def logger_setup():
    """Set up logging configuration based on environment variables and debug mode."""
    atexit.register(log_exit_code)

    # Loads up all the environment variables
    load_dotenv()
    debug = is_debug_on()
    today = datetime.now()

    logger_conf_path = Path(os.getenv("LOGGER_CONF_PATH", "logging.conf"))
    if debug:
        logger_conf_path = Path(os.getenv("LOGGER_CONF_DEV_PATH", "logging_dev.conf"))
    logger_folder_path = (
        f'{os.getenv("LOGGER_PATH", "./logs")}/{today.strftime("%Y-%m-%d")}'
    )

    try:
        Path(logger_folder_path).mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(
            f"Error creating log directory {Path(logger_folder_path)}: {e}",
            file=sys.stderr,
        )
        raise e

    logger_file_path = f'{logger_folder_path}/{today.strftime("%Y-%m-%dT%H%M%S")}.log'
    logger_db_table = os.getenv("LOGGER_DB_TABLE", "python_transfer_data_log")
    if logger_conf_path.exists():
        try:
            logging.config.fileConfig(
                logger_conf_path,
                defaults={
                    "logfilename": logger_file_path,
                    "table_name": logger_db_table,
                },
            )
        except Exception as e:
            print(
                f"Error setting up logging configuration from {logger_conf_path}: {e}",
                file=sys.stderr,
            )
            raise e
    else:
        logging.config.dictConfig(_default_logging_config(logger_file_path))
        if is_database_logging_on():
            log_db_handler = LogDBHandler(logger_db_table)
            logging.getLogger("").addHandler(log_db_handler)

    logger = logging.getLogger(__name__)
    logger.info("Setting up logger for %s", os.getenv("SCRIPT_NAME", Path.cwd().name))


class TimePeriod(Enum):
    """
    An enumeration representing various time periods with their corresponding singular and plural
    names, durations in seconds, and whether they support decimal representation.

    Attributes:
        ACT_YEAR (tuple): Represents an actual year (365.25 days).
        YEAR (tuple): Represents a year (365 days).
        DAY (tuple): Represents a day.
        HOUR (tuple): Represents an hour.
        MINUTE (tuple): Represents a minute.
        SECOND (tuple): Represents a second.
    """

    ACT_YEAR = (" year", " years", 31557600, False)
    YEAR = (" year", " years", 365 * 60 * 60 * 24, False)
    DAY = (" day", " days", 60 * 60 * 24, False)
    HOUR = ("h", "h", 60 * 60, False)
    MINUTE = ("m", "m", 60, False)
    SECOND = ("s", "s", 1, True)

    @property
    def single_name(self) -> str:
        """Returns the singular name."""
        return self.value[0]

    @property
    def multiple_name(self) -> str:
        """Returns the plural name."""
        return self.value[1]

    @property
    def seconds(self) -> int:
        """Returns the duration in seconds."""
        return self.value[2]

    @property
    def has_decimals(self) -> bool:
        """Indicates if decimals are supported."""
        return self.value[3]


def human_readable_time(seconds: int) -> str:
    """
    Convert a number of seconds into a human-readable string with periods going up to a year.

    Args:
        seconds (int): The number of seconds to convert.

    Returns:
        str: Human-readable string representing the time elapsed.
    """
    periods: list[TimePeriod] = [
        TimePeriod.ACT_YEAR,
        TimePeriod.YEAR,
        TimePeriod.DAY,
        TimePeriod.HOUR,
        TimePeriod.MINUTE,
        TimePeriod.SECOND,
    ]

    time_str = []
    skip_year = False
    for period in periods:
        if skip_year and period == TimePeriod.YEAR:
            continue
        if seconds >= period.seconds:
            period_value, seconds = divmod(seconds, period.seconds)
            if period == TimePeriod.ACT_YEAR and period_value > 0:
                skip_year = True
            if period.has_decimals:
                time_str.append(f"{period_value+seconds:.3f}{period.single_name}")
            else:
                time_str.append(
                    (
                        f"{int(period_value)}"
                        f"{period.multiple_name if period_value != 1 else period.single_name}"
                    )
                )

    return " ".join(time_str) if time_str else "0.000s"


def _default_logging_config(logger_file_path: str) -> None:
    """Return the default logging configuration.

    Args:
        logger_file_path (str): Path to the log file.

    Returns:
        dict: Default logging configuration dictionary.
    """
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "simple": {
                "format": "%(levelname)s | %(name)s | %(message)s",
                "datefmt": "%Y-%m-%dT%H:%M:%S",
            },
            "complex": {
                "format": "%(levelname)s | %(asctime)s | %(name)s | %(funcName)s | %(message)s",
                "datefmt": "%Y-%m-%dT%H:%M:%S",
            },
        },
        "handlers": {
            "screen": {
                "class": "logging.StreamHandler",
                "formatter": "simple",
                "level": "INFO" if is_debug_on() else "WARNING",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.FileHandler",
                "formatter": "complex",
                "level": "DEBUG" if is_debug_on() else "INFO",
                "filename": logger_file_path,
            },
        },
        "root": {
            "handlers": ["screen", "file"],
            "level": "DEBUG" if is_debug_on() else "INFO",
        },
    }
