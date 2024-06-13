import unittest
from dev_tools.custom_decorators import timing_decorator

class TestTimingDecorator(unittest.TestCase):
    def test_timing_decorator(self):
        @timing_decorator
        def sample_function(x, y):
            return x + y

        result = sample_function(1, 2)
        self.assertEqual(result, 3)

if __name__ == '__main__':
    unittest.main()
