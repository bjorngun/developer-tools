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
from types import TracebackType
from dotenv import load_dotenv

from .debug_tools import is_debug_on

# Mutable module-level holder for the process exit status. A dict is used (instead
# of a bare module global with the ``global`` statement) so the excepthook can
# record a non-zero status that ``log_exit_code`` reads at interpreter shutdown.
_exit_state: dict[str, int] = {"status": 0}


def is_same_day_append_enabled(override: bool | None = None) -> bool:
    """Check if logs should append to a stable file within the active folder.

    When enabled, repeated runs reuse the same basename instead of creating a
    timestamped file for each startup. This works well with
    ``TimedRotatingFileHandler`` because the handler can then rotate the active
    file at midnight while same-day runs continue to append to the current file.

    Args:
        override: Explicit value. When not ``None`` it takes precedence over the
            ``LOGGER_APPEND_SAME_DAY`` environment variable.
    """
    if override is not None:
        return override
    return os.getenv("LOGGER_APPEND_SAME_DAY", "False").lower() in ["true", "1", "t", "yes"]


def is_logs_sorted_by_days(override: bool | None = None) -> bool:
    """Check if logs should be sorted to a specific folder for each day.

    Args:
        override: Explicit value. When not ``None`` it takes precedence over the
            ``LOGGER_DAY_SPECIFIC`` environment variable.
    """
    if override is not None:
        return override
    return os.getenv("LOGGER_DAY_SPECIFIC", "False").lower() in ["true", "1", "t", "yes"]


def is_script_folders_enabled(override: bool | None = None) -> bool:
    """Check if script-specific log folders are enabled.
    
    When enabled, logs are organized into subfolders by script name:
        logs/{script_name}/2026/01/07/...
    
    Args:
        override: Explicit value. When not ``None`` it takes precedence over the
            ``LOGGER_SCRIPT_FOLDERS`` environment variable.

    Returns:
        True if script folders are enabled via argument or environment variable.
    """
    if override is not None:
        return override
    return os.getenv("LOGGER_SCRIPT_FOLDERS", "False").lower() in ["true", "1", "t", "yes"]


def _log_uncaught_exception(
    exc_type: type[BaseException],
    exc_value: BaseException,
    exc_traceback: TracebackType | None,
) -> None:
    """Record a non-zero exit status and log an uncaught exception's traceback.

    Installed as :data:`sys.excepthook` by :func:`logger_setup`. Capturing the
    failure here (rather than inspecting :func:`sys.exc_info` at ``atexit`` time,
    when the exception has already been cleared) ensures the traceback reaches
    the configured logging handlers and that :func:`log_exit_code` reports a
    truthful, non-zero exit code.

    After logging, the default :data:`sys.__excepthook__` is invoked so the
    standard stderr traceback is preserved (i.e. this hook augments rather than
    replaces the default behavior). ``KeyboardInterrupt`` is delegated straight
    to the default hook so Ctrl-C does not produce a noisy logged traceback,
    while still being recorded as a non-zero exit.
    """
    _exit_state["status"] = 1
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger = logging.getLogger(__name__)
    logger.critical(
        "Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback)
    )
    sys.__excepthook__(exc_type, exc_value, exc_traceback)


def log_exit_code() -> None:
    """Log the exit status recorded for the run.

    Logs ``1`` when :func:`_log_uncaught_exception` recorded an unhandled
    exception during the run, otherwise ``0``. This reflects the
    *uncaught-exception* status only: explicit ``sys.exit(N)`` / ``SystemExit``
    codes are not captured here, because :data:`sys.excepthook` is not invoked
    for ``SystemExit``.
    """
    logger = logging.getLogger(__name__)
    logger.info("Exit code: %s", _exit_state["status"])


def _get_logger_folder(
    script_name: str | None = None,
    now: datetime | None = None,
    *,
    logger_path: str | None = None,
    script_folders: bool | None = None,
    day_specific: bool | None = None,
) -> str:
    """Get the logger folder path, optionally including script-specific subfolder.
    
    Args:
        script_name: Optional script name for folder separation.
                     If None and script folders are enabled, 
                     falls back to SCRIPT_NAME env var.
        now: Optional pre-captured timestamp used to keep path/date
             calculations consistent with filename generation.
        logger_path: Explicit base log directory. Falls back to the
             ``LOGGER_PATH`` env var (default ``./logs``) when ``None``.
        script_folders: Explicit override for script-name subfolders.
             Falls back to ``LOGGER_SCRIPT_FOLDERS`` when ``None``.
        day_specific: Explicit override for per-day subfolders.
             Falls back to ``LOGGER_DAY_SPECIFIC`` when ``None``.
    
    Returns:
        Full path to the log folder, e.g.:
            ./logs/provisioning/2026/01/07/
    """
    today = now or datetime.now()
    base_path = logger_path or os.getenv("LOGGER_PATH", "./logs")

    # Add script-specific subfolder if enabled
    if is_script_folders_enabled(script_folders):
        effective_script = script_name or os.getenv("SCRIPT_NAME")
        if effective_script:
            base_path = f"{base_path}/{effective_script}"

    current_year = today.year
    logger_folder_path = f'{base_path}/{current_year}/{today.month:02d}'
    if is_logs_sorted_by_days(day_specific):
        logger_folder_path = f'{logger_folder_path}/{today.day:02d}'

    return logger_folder_path


def _get_log_basename(
    script_name: str | None = None,
    now: datetime | None = None,
    *,
    append_same_day: bool | None = None,
) -> str:
    """Return the log filename to use within the resolved log folder.

    Args:
        script_name: Optional script name for stable same-day filenames.
        now: Optional pre-captured timestamp for deterministic naming.
        append_same_day: Explicit override for same-day append behavior.
            Falls back to ``LOGGER_APPEND_SAME_DAY`` when ``None``.

    Returns:
        A timestamped filename when same-day append is disabled,
        otherwise a stable script-based basename.
    """
    current_time = now or datetime.now()
    if not is_same_day_append_enabled(append_same_day):
        return f'{current_time.strftime("%Y-%m-%dT%H%M%S")}.log'

    effective_script = script_name or os.getenv("SCRIPT_NAME") or Path.cwd().name
    safe_script_name = Path(effective_script).name.replace("/", "_").replace("\\", "_")
    return f"{safe_script_name}.log"


def logger_setup(
    script_name: str | None = None,
    *,
    logger_path: str | None = None,
    script_folders: bool | None = None,
    day_specific: bool | None = None,
    append_same_day: bool | None = None,
) -> None:
    """Set up logging configuration based on arguments, env vars, and debug mode.

    Call this once at the start of a script. It configures logging from a
    ``.conf`` file when present (or a sensible built-in default otherwise),
    writes logs to a structured folder hierarchy, and installs handlers so the
    final log line reports a truthful exit code (see :func:`log_exit_code`).

    Every behavioral option can be set explicitly via an argument **or** an
    environment variable. Arguments take precedence; when an argument is
    ``None`` the corresponding environment variable is used, which keeps
    deployment-time (12-factor) overrides working.

    Args:
        script_name: Script identifier for log folder/file separation.
            Falls back to the ``SCRIPT_NAME`` env var. When provided directly
            it applies to this call only and does not overwrite ``SCRIPT_NAME``
            for later calls in the same process.
        logger_path: Base log directory. Env var: ``LOGGER_PATH``
            (default ``./logs``).
        script_folders: Add a script-name subfolder before the year, i.e.
            ``{logger_path}/{script_name}/{year}/...``.
            Env var: ``LOGGER_SCRIPT_FOLDERS`` (default ``False``).
        day_specific: Add a zero-padded day subfolder.
            Env var: ``LOGGER_DAY_SPECIFIC`` (default ``False``).
        append_same_day: Reuse one stable log file per folder (named after the
            script) instead of creating a new timestamped file each run.
            Env var: ``LOGGER_APPEND_SAME_DAY`` (default ``False``).

    Additional environment variables (no argument equivalent):
        ``LOGGER_CONF_PATH`` (default ``logging.conf``) and
        ``LOGGER_CONF_DEV_PATH`` (default ``logging_dev.conf``) select the
        INI-style logging config file; ``DEBUG=True`` switches to the dev config
        and more verbose console output.

    Default vs. single-log-per-day:
        By default each run creates its own timestamped file, e.g.
        ``logs/2026/03/02/2026-03-02T062351.log`` (multi-log). To keep a single
        rolling log per day instead, enable same-day append::

            logger_setup(script_name="my_etl", append_same_day=True)
            # or, via environment:
            #   SCRIPT_NAME=my_etl
            #   LOGGER_APPEND_SAME_DAY=True

        Same-day runs then append to a stable file such as
        ``logs/2026/03/my_etl.log``; with the built-in
        ``TimedRotatingFileHandler`` (or the bundled ``logging.conf``) that file
        rotates at midnight, yielding one file per day.
    """
    # Install the exit handlers once. The excepthook records unhandled
    # exceptions so the exit code logged at shutdown reflects real failures.
    if sys.excepthook is not _log_uncaught_exception:
        sys.excepthook = _log_uncaught_exception
        atexit.register(log_exit_code)

    # Loads up all the environment variables
    load_dotenv()

    effective_script = script_name or os.getenv("SCRIPT_NAME")

    debug = is_debug_on()
    logger_conf_path = Path(os.getenv("LOGGER_CONF_PATH", "logging.conf"))
    if debug:
        logger_conf_path = Path(os.getenv("LOGGER_CONF_DEV_PATH", "logging_dev.conf"))
    current_time = datetime.now()
    logger_folder = _get_logger_folder(
        effective_script,
        now=current_time,
        logger_path=logger_path,
        script_folders=script_folders,
        day_specific=day_specific,
    )

    try:
        Path(logger_folder).mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(
            f"Error creating log directory {Path(logger_folder)}: {e}",
            file=sys.stderr,
        )
        raise e

    log_basename = _get_log_basename(
        effective_script, now=current_time, append_same_day=append_same_day
    )
    logger_file_path = f"{logger_folder}/{log_basename}"
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
