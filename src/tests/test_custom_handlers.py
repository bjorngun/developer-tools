from unittest.mock import patch, MagicMock, call
import logging
import os
from pathlib import Path
import pyodbc

from dev_tools.custom_handlers import LogDBHandler


class TestLogDBHandler:

    @patch("dev_tools.custom_handlers.pyodbc.connect")
    @patch("dev_tools.custom_handlers.os.getenv")
    def test_sql_connection_init_success(self, mock_getenv, mock_connect):
        mock_getenv.side_effect = lambda key: {
            "LOGGER_DB_SERVER": "test_server",
            "LOGGER_DB_NAME": "test_db",
            "LOGGER_SQL_DRIVER": "test_driver",
        }[key]

        mock_cursor = MagicMock()
        mock_connect.return_value.cursor.return_value = mock_cursor

        handler = LogDBHandler("test_table")
        assert handler.sql_cursor is not None
        mock_connect.assert_called_once()

    @patch("dev_tools.custom_handlers.pyodbc.connect")
    @patch("dev_tools.custom_handlers.os.getenv")
    def test_sql_connection_init_failure(self, mock_getenv, mock_connect, caplog):
        mock_getenv.side_effect = lambda key: {
            "LOGGER_DB_SERVER": "test_server",
            "LOGGER_DB_NAME": "test_db",
            "LOGGER_SQL_DRIVER": "test_driver",
        }[key]

        mock_connect.side_effect = pyodbc.Error("Connection error")

        with caplog.at_level(logging.ERROR, logger="sql_logger"):
            handler = LogDBHandler("test_table")
            assert handler.sql_cursor is None
            assert "Failed to connect to database: Connection error" in caplog.text

    @patch("dev_tools.custom_handlers.getpass.getuser", return_value="test_user")
    @patch("dev_tools.custom_handlers.datetime")
    @patch("dev_tools.custom_handlers.Path.cwd")
    @patch("dev_tools.custom_handlers.os.getenv")
    @patch("dev_tools.custom_handlers.pyodbc.connect")
    def test_emit(
        self, mock_connect, mock_getenv, mock_cwd, mock_datetime, mock_getuser
    ):
        mock_getenv.side_effect = lambda key, default=None: {
            "LOGGER_DB_SERVER": "test_server",
            "LOGGER_DB_NAME": "test_db",
            "LOGGER_SQL_DRIVER": "test_driver",
            "SCRIPT_NAME": "test_script",
        }.get(key, default)

        mock_cwd.return_value.name = "test_folder"
        mock_datetime.now.return_value.strftime.return_value = (
            "2024-06-18T12:00:00.000000"
        )

        mock_cursor = MagicMock()
        mock_connect.return_value.cursor.return_value = mock_cursor

        handler = LogDBHandler("test_table")
        logger = logging.getLogger("test_logger")
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)

        logger.debug("Test debug message")

        expected_call = call(
            "INSERT INTO [dbo].[test_table] ([log_level], [log_levelname], [log_module], [log_func], [log], [script], [created_at], [created_by], [pathname], [process_id]) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                10,
                "DEBUG",
                "test_logger",
                "test_emit",
                "Test debug message",
                "test_script",
                "2024-06-18T12:00:00.000000",
                "test_user",
                str(Path(__file__)),
                os.getpid(),
            ],
        )
        assert expected_call in mock_cursor.execute.call_args_list

    @patch("dev_tools.custom_handlers.getpass.getuser", return_value="test_user")
    @patch("dev_tools.custom_handlers.datetime")
    @patch("dev_tools.custom_handlers.Path.cwd")
    @patch("dev_tools.custom_handlers.os.getenv")
    @patch("dev_tools.custom_handlers.pyodbc.connect")
    def test_emit_long_message(
        self, mock_connect, mock_getenv, mock_cwd, mock_datetime, mock_getuser
    ):
        mock_getenv.side_effect = lambda key, default=None: {
            "LOGGER_DB_SERVER": "test_server",
            "LOGGER_DB_NAME": "test_db",
            "LOGGER_SQL_DRIVER": "test_driver",
            "SCRIPT_NAME": "test_script",
        }.get(key, default)

        mock_cwd.return_value.name = "test_folder"
        mock_datetime.now.return_value.strftime.return_value = (
            "2024-06-18T12:00:00.000000"
        )

        mock_cursor = MagicMock()
        mock_connect.return_value.cursor.return_value = mock_cursor

        handler = LogDBHandler("test_table")
        logger = logging.getLogger("test_logger")
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)

        long_message = "A" * 2050
        expected_message = f"{long_message[:2048 - len(LogDBHandler.MAX_LOG_MSG)]}{LogDBHandler.MAX_LOG_MSG}"

        logger.debug(long_message)

        expected_call = call(
            "INSERT INTO [dbo].[test_table] ([log_level], [log_levelname], [log_module], [log_func], [log], [script], [created_at], [created_by], [pathname], [process_id]) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                10,
                "DEBUG",
                "test_logger",
                "test_emit_long_message",
                expected_message,
                "test_script",
                "2024-06-18T12:00:00.000000",
                "test_user",
                str(Path(__file__)),
                os.getpid(),
            ],
        )
        assert expected_call in mock_cursor.execute.call_args_list
