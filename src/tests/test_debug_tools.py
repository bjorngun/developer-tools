import unittest
import os
from unittest.mock import patch
from dev_tools.debug_tools import is_debug_on, is_timing_on, logger_setup

class TestDebugTools(unittest.TestCase):
    @patch.dict(os.environ, {'DEBUG': 'true', 'TIMING': 'true'})
    def test_is_debug_on(self):
        self.assertTrue(is_debug_on())

    @patch.dict(os.environ, {'DEBUG': 'false', 'TIMING': 'true'})
    def test_is_timing_on(self):
        self.assertTrue(is_timing_on())

    @patch('dev_tools.debug_tools.logging.config.fileConfig')
    @patch('dev_tools.debug_tools.logging.config.dictConfig')
    def test_logger_setup(self, mock_dictConfig, mock_fileConfig):
        logger_setup()
        mock_dictConfig.assert_called()

if __name__ == '__main__':
    unittest.main()
