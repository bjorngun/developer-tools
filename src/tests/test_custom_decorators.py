from dev_tools.custom_decorators import timing_decorator


def test_timing_decorator():
    @timing_decorator
    def sample_function(x, y):
        return x + y

    result = sample_function(1, 2)
    assert result == 3
