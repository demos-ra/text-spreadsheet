"""What an integration reported as left behind, as it reported it.

Functions:
collect -- collect the names mtsv leaves behind while its body runs
"""

__all__ = ["collect"]

import logging
from contextlib import contextmanager
from typing import Iterator

# mtsv, What is left behind: the report goes to the mtsv.integrations
# logger at level WARNING, and the record carries the names, sorted, in
# its left_behind attribute.
_LOGGER = "mtsv.integrations"
_ATTRIBUTE = "left_behind"


class _Names(logging.Handler):
    """A handler that keeps the names a record carries."""

    def __init__(self, names: list[str]) -> None:
        """Keep the list the names are added to."""
        super().__init__()
        self.names = names

    def emit(self, record: logging.LogRecord) -> None:
        """Add the names of one report to the list."""
        self.names.extend(getattr(record, _ATTRIBUTE, ()))


@contextmanager
def collect() -> Iterator[list[str]]:
    """Collect the names mtsv leaves behind while its body runs.

    Yield the list, which is filled as the body runs and is complete
    once it ends.
    """
    names: list[str] = []
    logger = logging.getLogger(_LOGGER)
    handler = _Names(names)
    logger.addHandler(handler)
    try:
        yield names
    finally:
        logger.removeHandler(handler)
