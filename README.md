# Bosos Dev Tools

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white)](https://pypi.org/project/bosos-dev-tools/)
[![Platform](https://img.shields.io/badge/platform-linux%20%7C%20windows-lightgrey)](https://pypi.org/project/bosos-dev-tools/#files)
[![PyPI Version](https://img.shields.io/pypi/v/bosos-dev-tools)](https://pypi.org/project/bosos-dev-tools/#history)
[![PyPI status](https://img.shields.io/pypi/status/bosos-dev-tools.svg)](https://pypi.python.org/pypi/bosos-dev-tools/)
[![Test](https://github.com/bjorngun/developer-tools/actions/workflows/test.yml/badge.svg)](https://github.com/bjorngun/developer-tools/actions/workflows/test.yml)
[![Version & Release](https://github.com/bjorngun/developer-tools/actions/workflows/version.yml/badge.svg)](https://github.com/bjorngun/developer-tools/actions/workflows/version.yml)
[![codecov](https://codecov.io/gh/bjorngun/developer-tools/graph/badge.svg?token=LZKYK9IK5K)](https://codecov.io/gh/bjorngun/developer-tools)
[![License](https://img.shields.io/pypi/l/bosos-dev-tools)](LICENSE)

Bosos Dev Tools is a collection of utility tools for Python developers, designed to simplify debugging, logging, and monitoring tasks. This package includes decorators for measuring execution time, a progress bar utility, structured file logging, a markdown link checker, and an AST-based code map generator.

## Features

- **Custom Logging Handlers**: Log messages to various destinations with customizable formats.
- **Timing Decorators**: Easily measure the execution time of your functions with minimal code changes.
- **Progress Bar Utility**: Visualize the progress of long-running operations in the console.
- **Debug Tools**: Check if debug or timing modes are enabled via environment variables.
- **Markdown Link Checker**: Scan markdown files for broken internal links — available as a library and a CLI tool.
- **Code Map Generator**: Generate AST-based documentation artifacts (symbol index, dependency graph, entry points, call graph) for any Python package.

## Installation

You can install the package via pip:

```sh
pip install bosos-dev-tools
```

## Usage

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

Visualize the progress of long-running iterations in the console.

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
from dev_tools.logger_settings import logger_setup

def main():
    logger_setup()

if __name__ == '__main__':
    main()
```

Log files are written to a structured folder hierarchy:

```
logs/
  2026/
    03/
      02/
        2026-03-02T062351.log
```

The folder path is controlled by environment variables:

| Variable | Default | Description |
|---|---|---|
| `LOGGER_PATH` | `./logs` | Base log directory |
| `LOGGER_DAY_SPECIFIC` | `False` | Add a day subfolder (zero-padded) |
| `LOGGER_SCRIPT_FOLDERS` | `False` | Add a script-name subfolder before the year |

#### Logging Configuration File

`logger_setup()` looks for an INI-style logging config file in the current working directory:

- **Normal mode:** `logging.conf` (override with `LOGGER_CONF_PATH`)
- **Debug mode** (`DEBUG=True`): `logging_dev.conf` (override with `LOGGER_CONF_DEV_PATH`)

If the config file is not found, a sensible **built-in default** is used automatically — no `.conf` file is required. The default configuration writes to both a file handler (all messages) and a console handler (warnings only; or all messages in debug mode).

| Variable | Default | Description |
|---|---|---|
| `LOGGER_CONF_PATH` | `logging.conf` | Path to the logging config file |
| `LOGGER_CONF_DEV_PATH` | `logging_dev.conf` | Path to the debug logging config file |
| `DEBUG` | `False` | Enable debug mode (verbose console output) |

### Markdown Link Checker

Scan markdown files for broken internal links. Available as a library or a CLI tool.

**As a library:**

``` py
from dev_tools.md_link_checker import scan_all
from pathlib import Path

result = scan_all(Path("."))
for r in result.results:
    if r.status == "broken":
        print(f"{r.source_file}:{r.line_number} -> {r.target} ({r.reason})")
```

**As a CLI:**

```sh
# Installed console script
md-link-checker --verbose

# Or run as a module
python -m dev_tools.md_link_checker --no-anchors --json
```

### Code Map Generator

Generate AST-based documentation for a Python package — symbol index, dependency graph, entry points, and call graph.

**As a library:**

``` py
from pathlib import Path
from dev_tools.codemap_generator import CodeMapGenerator

gen = CodeMapGenerator(src_root=Path("src"), package_name="my_package")
gen.analyze()
gen.write_outputs(output_dir=Path("docs"))
```

**As a CLI:**

```sh
# Installed console script
codemap-generator --package my_package

# Or run as a module
python -m dev_tools.codemap_generator --package my_package --output-dir docs
```

## License

This project is licensed under the MIT License. See the [LICENSE](https://github.com/bjorngun/developer-tools/blob/main/LICENSE) file for more details.

## Links

- **Source Code**: [GitHub Repository](https://github.com/bjorngun/developer-tools)
- **Issue Tracker**: [GitHub Issues](https://github.com/bjorngun/developer-tools/issues)
- **Changelog**: [CHANGELOG.md](https://github.com/bjorngun/developer-tools/blob/main/CHANGELOG.md)
