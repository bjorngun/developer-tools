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
    """Determine if debug mode is enabled."""
    return os.getenv('DEBUG', 'False').lower() in ['true', '1', 't', 'yes']

def is_timing_on() -> bool:
    """Determine if timing mode is enabled."""
    return os.getenv('TIMING', 'False').lower() in ['true', '1', 't', 'yes']

def is_database_logging_on() -> bool:
    """Determine if database logging mode is enabled."""
    return os.getenv('LOGGER_DATABASE', 'False').lower() in ['true', '1', 't', 'yes']

def log_exit_code():
    """Log the exit code of the script."""
    logger = logging.getLogger(__name__)
    exit_code = 0 if sys.exc_info() == (None, None, None) else 1
    logger.info(f'Exit code: {exit_code}')
    
def default_logging_config(logger_file_path: str):
    """Default logging configuration."""
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

def logger_setup():
    """Set up logging configuration based on environment variables and debug mode."""
    atexit.register(log_exit_code)

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
            })
        except Exception as e:
            print(f'Error setting up logging configuration from {logger_conf_path}: {e}', file=sys.stderr)
            sys.exit(1)
    else:
        logging.config.dictConfig(default_logging_config(logger_file_path))
        if (is_database_logging_on()):
            log_db_handler = LogDBHandler(logger_db_table)
            logging.getLogger('').addHandler(log_db_handler)

    logger = logging.getLogger(__name__)
    logger.info(f'Setting up logger for {os.getenv("SCRIPT_NAME", Path.cwd().name)}')
