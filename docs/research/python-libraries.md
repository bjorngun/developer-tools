# Python Libraries

> Python packages, APIs, stdlib modules relevant to `bosos-dev-tools`.

## Python stdlib logging file strategies

**Source:** [Logging HOWTO](https://docs.python.org/3/howto/logging.html) ; [logging.handlers](https://docs.python.org/3/library/logging.handlers.html) ; [Logging Cookbook](https://docs.python.org/3/howto/logging-cookbook.html)
**Date Researched:** 2026-06-04
**Relevance:** `dev_tools.logger_settings` currently generates a timestamped base filename per run, which prevents same-day append behavior even though the shipped config already uses `TimedRotatingFileHandler`.

### Summary

Python's standard `FileHandler` appends by default because its default mode is `'a'`, and the logging HOWTO explicitly notes that repeated runs append to the same file unless `filemode='w'` is used. `TimedRotatingFileHandler` also writes to a stable base filename and rotates it on schedule, which makes it a good fit for one active file per day if the base filename itself stays constant. The main caveat is concurrency: the logging cookbook says logging to a single file from multiple processes is not supported, so same-file append is a good default for single-process tools, but not for multi-process workloads.

### Key Points

- `FileHandler(filename, mode='a', ...)` appends by default, so append behavior is already the stdlib default when the filename is stable.
- The logging HOWTO states that repeated runs append to the same file unless `filemode='w'` is specified.
- `TimedRotatingFileHandler(..., when='midnight', ...)` rotates based on time while continuing to write to the same active base file until rollover; this is the most direct stdlib option for "one file per day" behavior.
- `RotatingFileHandler` is the size-based alternative when bounded file size matters more than calendar-based grouping.
- `WatchedFileHandler` is mainly for Unix/Linux logrotate-style setups and is not appropriate for Windows.
- The logging cookbook explicitly says logging to a single file from multiple processes is not supported; use `QueueHandler`/`QueueListener` or a socket listener if separate processes must share one logical log.
- The logging HOWTO advises library authors not to add real handlers in library code; applications should own handler configuration. For `bosos-dev-tools`, that means any same-day append behavior should be optional and caller-controlled rather than the only behavior.

### See Also

- [Research Index](index.md)
