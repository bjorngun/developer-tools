"""
logger_settings.py

This module provides utilities for setting up logging configuration, including functions to
configure log paths, file handlers, and console output based on environment variables.
"""

import atexit
from datetime import datetime
import logging
import logging.config
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from .debug_tools import is_debug_on


def is_same_day_append_enabled() -> bool:
    """Check if logs should append to a stable file within the active folder.

    When enabled, repeated runs reuse the same basename instead of creating a
    timestamped file for each startup. This works well with
    ``TimedRotatingFileHandler`` because the handler can then rotate the active
    file at midnight while same-day runs continue to append to the current file.
    """
    return os.getenv("LOGGER_APPEND_SAME_DAY", "False").lower() in ["true", "1", "t", "yes"]


def is_logs_sorted_by_days() -> bool:
    """Check if logs should be sorted to a specific folder for each day"""
    return os.getenv("LOGGER_DAY_SPECIFIC", "False").lower() in ["true", "1", "t", "yes"]


def is_script_folders_enabled() -> bool:
    """Check if script-specific log folders are enabled via environment variable.
    
    When enabled, logs are organized into subfolders by script name:
        logs/{script_name}/2026/01/07/...
    
    Returns:
        True if LOGGER_SCRIPT_FOLDERS is set to a truthy value.
    """
    return os.getenv("LOGGER_SCRIPT_FOLDERS", "False").lower() in ["true", "1", "t", "yes"]


def log_exit_code() -> None:
    """Log the exit code of the script."""
    logger = logging.getLogger(__name__)
    exit_code = 0 if sys.exc_info() == (None, None, None) else 1
    logger.info("Exit code: %s", exit_code)


def _get_logger_folder(script_name: str | None = None, now: datetime | None = None) -> str:
    """Get the logger folder path, optionally including script-specific subfolder.
    
    Args:
        script_name: Optional script name for folder separation.
                     If None and LOGGER_SCRIPT_FOLDERS is enabled, 
                     falls back to SCRIPT_NAME env var.
        now: Optional pre-captured timestamp used to keep path/date
             calculations consistent with filename generation.
    
    Returns:
        Full path to the log folder, e.g.:
            ./logs/provisioning/2026/01/07/
    """
    today = now or datetime.now()
    logger_path = os.getenv("LOGGER_PATH", "./logs")

    # Add script-specific subfolder if enabled
    if is_script_folders_enabled():
        effective_script = script_name or os.getenv("SCRIPT_NAME")
        if effective_script:
            logger_path = f"{logger_path}/{effective_script}"

    current_year = today.year
    logger_folder_path = f'{logger_path}/{current_year}/{today.month:02d}'
    if is_logs_sorted_by_days():
        logger_folder_path = f'{logger_folder_path}/{today.day:02d}'

    return logger_folder_path


def _get_log_basename(script_name: str | None = None, now: datetime | None = None) -> str:
    """Return the log filename to use within the resolved log folder.

    Args:
        script_name: Optional script name for stable same-day filenames.
        now: Optional pre-captured timestamp for deterministic naming.

    Returns:
        A timestamped filename when LOGGER_APPEND_SAME_DAY is disabled,
        otherwise a stable script-based basename.
    """
    current_time = now or datetime.now()
    if not is_same_day_append_enabled():
        return f'{current_time.strftime("%Y-%m-%dT%H%M%S")}.log'

    effective_script = script_name or os.getenv("SCRIPT_NAME") or Path.cwd().name
    safe_script_name = Path(effective_script).name.replace("/", "_").replace("\\", "_")
    return f"{safe_script_name}.log"


def logger_setup(script_name: str | None = None) -> None:
    """Set up logging configuration based on environment variables and debug mode.
    
    Args:
        script_name: Optional script identifier for log folder separation.
                     If provided and LOGGER_SCRIPT_FOLDERS=True, logs go to:
                         {LOGGER_PATH}/{script_name}/{year}/{month}/{day}/
                     If LOGGER_APPEND_SAME_DAY=True, repeated runs append to
                     a stable basename in that folder instead of creating a
                     new timestamped filename each run.
    """
    atexit.register(log_exit_code)

    # Loads up all the environment variables
    load_dotenv()

    effective_script = script_name or os.getenv("SCRIPT_NAME")

    debug = is_debug_on()
    logger_conf_path = Path(os.getenv("LOGGER_CONF_PATH", "logging.conf"))
    if debug:
        logger_conf_path = Path(os.getenv("LOGGER_CONF_DEV_PATH", "logging_dev.conf"))
    current_time = datetime.now()
    logger_path = _get_logger_folder(effective_script, now=current_time)

    try:
        Path(logger_path).mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(
            f"Error creating log directory {Path(logger_path)}: {e}",
            file=sys.stderr,
        )
        raise e

    logger_file_path = f"{logger_path}/{_get_log_basename(effective_script, now=current_time)}"
    if logger_conf_path.exists():
        try:
            logging.config.fileConfig(
                logger_conf_path,
                defaults={
                    "logfilename": logger_file_path,
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

    logger = logging.getLogger(__name__)
    logger.info("Setting up logger for %s", effective_script or Path.cwd().name)


def _default_logging_config(logger_file_path: str) -> dict[str, object]:
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
                "class": "logging.handlers.TimedRotatingFileHandler",
                "formatter": "complex",
                "level": "DEBUG" if is_debug_on() else "INFO",
                "filename": logger_file_path,
                "when": "midnight",
                "interval": 1,
                "backupCount": 5,
                "encoding": "utf-8",
            },
        },
        "root": {
            "handlers": ["screen", "file"],
            "level": "DEBUG" if is_debug_on() else "INFO",
        },
    }
