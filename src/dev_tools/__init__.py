"""
__init__.py

This package provides a suite of tools and utilities for debugging, logging, and monitoring progress
in Python applications. Included modules are:

- custom_decorators: Provides decorators for measuring and logging function execution time.
- custom_handlers: Contains custom logging handlers, including a handler that logs messages to a SQL
  database.
- debug_tools: Offers utilities for checking debug and timing settings and logging exceptions.
- progress_bar: Implements a progress bar for iterables with support for debugging and timing
  estimations.
"""

from dev_tools.progress_bar import progress_bar
from dev_tools.custom_decorators import timing_decorator
from dev_tools.custom_handlers import LogDBHandler
from dev_tools.debug_tools import is_debug_on
from dev_tools.logger_settings import logger_setup

__all__ = [
    "logger_setup",
    "is_debug_on",
    "progress_bar",
    "timing_decorator",
    "LogDBHandler",
]
