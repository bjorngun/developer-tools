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
from dotenv import load_dotenv

from .custom_handlers import LogDBHandler
from .debug_tools import is_debug_on


def is_database_logging_on() -> bool:
    """Check if database logging is enabled via environment variable."""
    return os.getenv("LOGGER_DATABASE", "False").lower() in ["true", "1", "t", "yes"]


def is_logs_sorted_by_days() -> bool:
    """Check if logs should be sorted to a specific folder for each day"""
    return os.getenv("LOGGER_DAY_SPECIFIC", "False").lower() in ["true", "1", "t", "yes"]


def is_script_folders_enabled() -> bool:
    """Check if script-specific log folders are enabled via environment variable.
    
    When enabled, logs are organized into subfolders by script name:
        logs/{script_name}/2026/1.January/7/...
    
    Returns:
        True if LOGGER_SCRIPT_FOLDERS is set to a truthy value.
    """
    return os.getenv("LOGGER_SCRIPT_FOLDERS", "False").lower() in ["true", "1", "t", "yes"]


def log_exit_code() -> None:
    """Log the exit code of the script."""
    logger = logging.getLogger(__name__)
    exit_code = 0 if sys.exc_info() == (None, None, None) else 1
    logger.info("Exit code: %s", exit_code)


def _get_logger_folder(script_name: str | None = None) -> str:
    """Get the logger folder path, optionally including script-specific subfolder.
    
    Args:
        script_name: Optional script name for folder separation.
                     If None and LOGGER_SCRIPT_FOLDERS is enabled, 
                     falls back to SCRIPT_NAME env var.
    
    Returns:
        Full path to the log folder, e.g.:
            ./logs/provisioning/2026/1.January/7/
    """
    today = datetime.now()
    logger_path = os.getenv("LOGGER_PATH", "./logs")

    # Add script-specific subfolder if enabled
    if is_script_folders_enabled():
        effective_script = script_name or os.getenv("SCRIPT_NAME")
        if effective_script:
            logger_path = f"{logger_path}/{effective_script}"

    current_year = today.year
    current_month = f'{today.month}.{today.strftime("%B")}'
    logger_folder_path = (
        f'{logger_path}/{current_year}/{current_month}'
    )
    if is_logs_sorted_by_days():
        logger_folder_path = f'{logger_folder_path}/{today.day}'

    return logger_folder_path


def logger_setup(script_name: str | None = None) -> None:
    """Set up logging configuration based on environment variables and debug mode.
    
    Args:
        script_name: Optional script identifier for log folder separation.
                     If provided and LOGGER_SCRIPT_FOLDERS=True, logs go to:
                         {LOGGER_PATH}/{script_name}/{year}/{month}/{day}/
                     Also sets SCRIPT_NAME env var for LogDBHandler compatibility.
    """
    atexit.register(log_exit_code)

    # Loads up all the environment variables
    load_dotenv()

    # Set SCRIPT_NAME env var if provided (for LogDBHandler and folder path)
    if script_name:
        os.environ["SCRIPT_NAME"] = script_name

    debug = is_debug_on()
    today = datetime.now()

    logger_conf_path = Path(os.getenv("LOGGER_CONF_PATH", "logging.conf"))
    if debug:
        logger_conf_path = Path(os.getenv("LOGGER_CONF_DEV_PATH", "logging_dev.conf"))
    logger_path = _get_logger_folder(script_name)

    try:
        Path(logger_path).mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(
            f"Error creating log directory {Path(logger_path)}: {e}",
            file=sys.stderr,
        )
        raise e

    logger_file_path = f'{logger_path}/{today.strftime("%Y-%m-%dT%H%M%S")}.log'
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
