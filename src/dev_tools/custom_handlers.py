"""
custom_handlers.py

This module provides custom logging handlers, including a handler that logs messages to a SQL
database.
"""

import logging
import os
from datetime import datetime
import getpass
from pathlib import Path
import pyodbc


class LogDBHandler(logging.Handler):
    """
    A custom logging handler that logs messages to a SQL database.

    This handler overrides the logging.Handler class to provide functionality for logging messages
    to a SQL database. It manages the SQL connection and handles the insertion of log records into
    the specified database table.

    Attributes:
        MAX_LOG_LEN (int): Maximum length for the log message to be stored in the database.
        MAX_LOG_MSG (str): Message to append if the log message is truncated.
    """

    MAX_LOG_LEN = 2048
    MAX_LOG_MSG = "... too long, check the local logs to see the full msg"

    def __init__(self, db_table: str):
        """Initializes the handler and the SQL connection."""
        logging.Handler.__init__(self)
        self.sql_cursor = self._get_sql_connection()
        self.db_table = db_table

    def emit(self, record):
        """Emits a record to the database."""

        if self.sql_cursor is None:
            return

        # Ensure message is a string and escape quotes if necessary
        try:
            msg = str(record.msg).replace("'", "''")
        except Exception as e:
            logging.getLogger("sql_logger").error("Error processing log message: %s", e)
            raise e

        # Truncate the log message if it exceeds the maximum length
        if len(msg) > self.MAX_LOG_LEN:
            msg = f"{msg[:self.MAX_LOG_LEN - len(self.MAX_LOG_MSG)]}{self.MAX_LOG_MSG}"

        # Set current time
        current_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")

        # Database columns for the log entry
        db_columns = [
            "log_level",
            "log_levelname",
            "log_module",
            "log_func",
            "log",
            "script",
            "created_at",
            "created_by",
            "pathname",
            "process_id",
        ]

        # Values for the log entry
        row_values = [
            record.levelno,
            record.levelname,
            record.name,
            record.funcName,
            msg,
            os.getenv("SCRIPT_NAME", Path.cwd().name),
            current_time,
            getpass.getuser(),
            record.pathname,
            os.getpid(),
        ]

        # Insert the log entry into the database
        try:
            self._insert_log(self.db_table, db_columns, row_values)
        except Exception: # pylint: disable=broad-exception-caught
            self.handleError(record)

    def _get_sql_connection(self):
        """Initializes connection to a database."""
        try:
            connection_string = (
                f'SERVER={os.getenv("LOGGER_DB_SERVER")};'
                f'DATABASE={os.getenv("LOGGER_DB_NAME")};'
                f'DRIVER={os.getenv("LOGGER_SQL_DRIVER")};'
                "Trusted_Connection=yes;"
            )

            conn = pyodbc.connect(
                connection_string,
                autocommit=True,
                TrustServerCertificate="YES",
            )
            cursor = conn.cursor()
            return cursor
        except pyodbc.Error as e:
            logging.getLogger("sql_logger").error(
                "Failed to connect to database: %s", e
            )
            return None

    def _insert_log(self, table: str, columns: list[str], values: list):
        """Executes Insert statement in the connected database.

        Args:
            table (str): Name of the table being inserted into
            columns (list[str]): List of names of the columns that are being inserted into
            values (list): List of the values
        """
        if self.sql_cursor is None:
            return

        table = f"[dbo].[{table}]"
        header = ", ".join([f"[{x}]" for x in columns])
        parameters = ", ".join(["?"] * len(columns))

        try:
            self.sql_cursor.execute(
                f"INSERT INTO {table} ({header}) VALUES({parameters})", values
            )
        except pyodbc.Error as e:
            sql_state = e.args[0]
            if sql_state == "28000":
                logging.getLogger("sql_logger").error(
                    "LDAP Connection failed: check password"
                )
            else:
                sql_state_msg = e.args[1]
                logging.getLogger("sql_logger").error(
                    "Error executing insert statement: %s", sql_state_msg
                )
        except TypeError as e:
            logging.getLogger("sql_logger").error(
                "Type error with provided values: %s", e
            )
        except Exception as e:
            logging.getLogger("sql_logger").error("Unexpected error: %s", e)
            raise e
