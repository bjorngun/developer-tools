import logging
import os
from datetime import datetime
import pyodbc
import getpass
from pathlib import Path


class LogDBHandler(logging.Handler):
    """Customized logging handler that puts logs to the database."""

    class SQLLogConnection:
        """Connection class for a SQL database."""

        def __init__(self):
            """Initializes connection to a database."""
            try:
                connection_string = (f'SERVER={os.getenv("LOGGER_DB_SERVER")};'
                                    f'DATABASE={os.getenv("LOGGER_DB_NAME")};'
                                    f'DRIVER={os.getenv("LOGGER_SQL_DRIVER")};'
                                    'Trusted_Connection=yes;')

                conn = pyodbc.connect(
                    connection_string,
                    autocommit=True,
                    TrustServerCertificate='YES',
                )
                self.cursor = conn.cursor()
            except pyodbc.Error as e:
                logging.getLogger('sql_logger').error(f"Error connecting to database: {e}")
                self.cursor = None

        def insert(self, table: str, columns: list[str], values: list):
            """Executes Insert statement in the connected database.

            Args:
                table (str): Name of the table being inserted into
                columns (list[str]): List of names of the columns that are being inserted into
                values (list): List of the values
            """
            if self.cursor is None:
                logging.getLogger('sql_logger').error("No database connection available.")
                return

            table = f'[dbo].[{table}]'
            header = ', '.join([f'[{x}]' for x in columns])
            parameters = ', '.join(['?']*len(columns))

            try:
                self.cursor.execute(
                    f'INSERT INTO {table} ({header}) VALUES({parameters})', values)
            except pyodbc.Error as e:
                logging.getLogger('sql_logger').error(f"Error executing insert statement: {e}")
            except TypeError as e:
                logging.getLogger('sql_logger').error(f"Type error with provided values: {e}")
            except Exception as e:
                logging.getLogger('sql_logger').error(f"Unexpected error: {e}")

    # Maximum length for the log message to be stored in the database
    MAX_LOG_LEN = 2048
    # Message to append if the log message is truncated
    MAX_LOG_MSG = '... too long, check the local logs to see the full msg'

    def __init__(self, db_table: str):
        """Initializes the handler and the SQL connection."""
        logging.Handler.__init__(self)
        self.sql_connection = self.SQLLogConnection()
        self.db_table = db_table

    def emit(self, record):
        """Emits a record to the database."""

        # Ensure message is a string and escape quotes if necessary
        try:
            log_message = str(record.msg).replace("'", "''")
        except Exception as e:
            logging.getLogger('sql_logger').error(f"Error processing log message: {e}")
            return

        # Truncate the log message if it exceeds the maximum length
        if len(log_message) > self.MAX_LOG_LEN:
            log_message = f'{log_message[:self.MAX_LOG_LEN - len(self.MAX_LOG_MSG)]}{self.MAX_LOG_MSG}'

        # Set current time
        current_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")

        # Database columns for the log entry
        db_columns = [
            'log_level',
            'log_levelname',
            'log_module',
            'log_func',
            'log',
            'script',
            'created_at',
            'created_by',
            'pathname',
            'process_id',
        ]

        # Values for the log entry
        row_values = [
            record.levelno,
            record.levelname,
            record.name,
            record.funcName,
            log_message,
            os.getenv("SCRIPT_NAME", Path.cwd().name),
            current_time,
            getpass.getuser(),
            record.pathname,
            os.getpid(),
        ]

        # Insert the log entry into the database
        try:
            self.sql_connection.insert(self.db_table, db_columns, row_values)
        except Exception as e:
            logging.getLogger('sql_logger').error(f"Error inserting log into database: {e}")
