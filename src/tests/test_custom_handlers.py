import unittest
from unittest.mock import patch
import logging
from dev_tools.custom_handlers import LogDBHandler

class TestLogDBHandler(unittest.TestCase):
    @patch('dev_tools.custom_handlers.pyodbc.connect')
    def test_emit(self, mock_connect):
        mock_connect.return_value.cursor.return_value.execute.return_value = None

        logger = logging.getLogger('test_logger')
        db_handler = LogDBHandler(db_table='test_table')
        logger.addHandler(db_handler)
        logger.setLevel(logging.INFO)

        with self.assertLogs('test_logger', level='INFO') as log:
            logger.info('This is a test log message')

        self.assertIn('This is a test log message', log.output[0])

if __name__ == '__main__':
    unittest.main()
