import unittest
import os
from unittest.mock import patch
from dev_tools.progress_bar import progress_bar

class TestProgressBar(unittest.TestCase):
    
    @patch('builtins.print')
    @patch.dict(os.environ, {'DEBUG': 'true', 'TIMING': 'true'})
    def test_progress_bar(self, mock_print):
        items = list(range(10))
        result = list(progress_bar(items))

        self.assertEqual(result, items)
        self.assertTrue(mock_print.called)

if __name__ == '__main__':
    unittest.main()
