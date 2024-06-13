import atexit
from datetime import datetime
import logging
import logging.config
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from .custom_handlers import LogDBHandler


def is_debug_on() -> bool:
    """Check if debug mode is enabled via environment variable."""
    return os.getenv('DEBUG', 'False').lower() in ['true', '1', 't', 'yes']

def is_timing_on() -> bool:
    """Check if timing mode is enabled via environment variable."""
    return os.getenv('TIMING', 'False').lower() in ['true', '1', 't', 'yes']

def is_database_logging_on() -> bool:
    """Check if database logging is enabled via environment variable."""
    return os.getenv('LOGGER_DATABASE', 'False').lower() in ['true', '1', 't', 'yes']

def logger_setup():
    """Set up logging configuration based on environment variables and debug mode."""
    atexit.register(_log_exit_code)

    #Loads up all the environment variables
    load_dotenv()
    debug = is_debug_on()
    today = datetime.now()

    logger_conf_path = Path(os.getenv('LOGGER_CONF_PATH', 'logging.conf'))
    if debug:
        logger_conf_path = Path(os.getenv('LOGGER_CONF_DEV_PATH', 'logging_dev.conf'))
    logger_folder_path = f'{os.getenv("LOGGER_PATH", "./logs")}/{today.strftime("%Y-%m-%d")}'

    try:
        Path(logger_folder_path).mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f'Error creating log directory {Path(logger_folder_path)}: {e}', file=sys.stderr)
        sys.exit(1)

    logger_file_path = f'{logger_folder_path}/{today.strftime("%Y-%m-%dT%H%M%S")}.log'
    logger_db_table = os.getenv('LOGGER_DB_TABLE', 'python_transfer_data_log')
    if logger_conf_path.exists():
        try:
            logging.config.fileConfig(logger_conf_path, defaults={
                'logfilename': logger_file_path,
                'table_name': logger_db_table,
            })
        except Exception as e:
            print(f'Error setting up logging configuration from {logger_conf_path}: {e}', file=sys.stderr)
            sys.exit(1)
    else:
        logging.config.dictConfig(_default_logging_config(logger_file_path))
        if (is_database_logging_on()):
            log_db_handler = LogDBHandler(logger_db_table)
            logging.getLogger('').addHandler(log_db_handler)

    logger = logging.getLogger(__name__)
    logger.info(f'Setting up logger for {os.getenv("SCRIPT_NAME", Path.cwd().name)}')

from enum import Enum

class TimePeriod(Enum):
    YEAR = (' year', ' years', 60 * 60 * 24 * 365, False)
    DAY = (' day', ' days', 60 * 60 * 24, False)
    HOUR = ('h', 'h', 60 * 60, False)
    MINUTE = ('m', 'm', 60, False)
    SECOND = ('s', 's', 1, True)

    @property
    def name(self) -> str:
        return self.value[0]
    
    @property
    def multiple_name(self) -> str:
        return self.value[1]

    @property
    def seconds(self) -> int:
        return self.value[2]

    @property
    def has_decimals(self) -> bool:
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
        TimePeriod.YEAR,
        TimePeriod.DAY,
        TimePeriod.HOUR,
        TimePeriod.MINUTE,
        TimePeriod.SECOND,
    ]

    time_str = []
    for period in periods:
        if seconds >= period.seconds:
            period_value, seconds = divmod(seconds, period.seconds)
            if period.has_decimals:
                time_str.append(f"{period_value+seconds:.3f}{period.name}")
            else:
                time_str.append(f"{int(period_value)}{period.multiple_name if period_value != 1 else period.name}")

    return ' '.join(time_str) if time_str else '0.000s'

# Example usage:
print(human_readable_time(12345678.6343))  # Output: "142 days, 21 hours, 21 minutes, 18 seconds"

def _log_exit_code() -> None:
    """Log the exit code of the script."""
    logger = logging.getLogger(__name__)
    exit_code = 0 if sys.exc_info() == (None, None, None) else 1
    logger.info(f'Exit code: {exit_code}')

    
def _default_logging_config(logger_file_path: str) -> None:
    """Return the default logging configuration.

    Args:
        logger_file_path (str): Path to the log file.

    Returns:
        dict: Default logging configuration dictionary.
    """
    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'simple': {
                'format': '%(levelname)s | %(name)s | %(message)s',
                'datefmt': '%Y-%m-%dT%H:%M:%S',
            },
            'complex': {
                'format': '%(levelname)s | %(asctime)s | %(name)s | %(funcName)s | %(message)s',
                'datefmt': '%Y-%m-%dT%H:%M:%S',
            },
        },
        'handlers': {
            'screen': {
                'class': 'logging.StreamHandler',
                'formatter': 'simple',
                'level': 'INFO' if is_debug_on() else 'WARNING',
                'stream': 'ext://sys.stdout',
            },
            'file': {
                'class': 'logging.FileHandler',
                'formatter': 'complex',
                'level': 'DEBUG' if is_debug_on() else 'INFO',
                'filename': logger_file_path,
            },
        },
        'root': {
            'handlers': ['screen', 'file'],
            'level': 'DEBUG' if is_debug_on() else 'INFO',
        },
    }
