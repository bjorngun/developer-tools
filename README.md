# Bosos Dev Tools

Bosos Dev Tools is a collection of utility tools for Python developers, designed to simplify debugging, logging, and monitoring tasks. This package includes custom logging handlers, decorators for measuring execution time, and a progress bar utility to enhance the development workflow.

## Features

- **Custom Logging Handlers**: Log messages to various destinations, including databases, with customizable formats.
- **Timing Decorators**: Easily measure the execution time of your functions with minimal code changes.
- **Progress Bar Utility**: Visualize the progress of long-running operations in the console.
- **Debug Tools**: Check if debug or timing modes are enabled via environment variables.

## Installation

You can install the package via pip:

```sh
pip install bosos-dev-tools
```

## Usage

### Custom Logging Handler

The `LogDBHandler` allows you to log messages directly to a database.

``` py
import logging
from dev_tools.custom_handlers import LogDBHandler

logger = logging.getLogger('test_logger')
db_handler = LogDBHandler(db_table='test_table')
logger.addHandler(db_handler)
logger.setLevel(logging.INFO)

logger.info('This is a test log message.')
```

### Timing Decorator

Use the `timing_decorator` to measure the execution time of functions.

``` py
from dev_tools.custom_decorators import timing_decorator

@timing_decorator
def example_function():
    for i in range(1000000):
        pass

example_function()
```

### Progress Bar

Use the `progress_bar` to measure the execution time of functions.

``` py
from dev_tools.progress_bar import progress_bar

for item in progress_bar(range(10)):
    pass
```

### Debug Tools

Check if debug or timing modes are enabled via environment variables.
Use the `logger_setup` to set up your logging settings at the beginning of the script.

``` py
from dev_tools.debug_tools import is_debug_on, is_timing_on

print('Is debug on:', is_debug_on())
print('Is timing on:', is_timing_on())
```

``` py
from dev_tools.debug_tools import logger_setup

def main():
    logger_setup()

if __name__ == '__main__':
    main()
```

## License

This project is licensed under the MIT License. See the [LICENSE](https://github.com/bjorngun/developer-tools/blob/main/LICENSE) file for more details.

## Links

- **Source Code**: [GitHub Repository](https://github.com/bjorngun/developer-tools)
- **Issue Tracker**: [GitHub Issues](https://github.com/bjorngun/developer-tools/issues)
