"""What an integration reported as left behind, as it reported it.

Functions:
collect -- collect the names mtsv leaves behind in this thread
"""

__all__ = ["collect"]

import logging
import threading
from contextlib import contextmanager
from typing import Iterator

# mtsv, What is left behind: the report goes to the mtsv.integrations
# logger at level WARNING, and the record carries the names, sorted, in
# its left_behind attribute.
_LOGGER = "mtsv.integrations"
_ATTRIBUTE = "left_behind"


@contextmanager
def collect() -> Iterator[list[str]]:
    """Collect the names mtsv leaves behind in this thread.

    Yield the list, which is filled as the body runs and is complete
    once it ends. MCP Python SDK, Tools: a plain function runs in a
    thread, so a report made in another thread is another call's.
    """
    names: list[str] = []
    logger = logging.getLogger(_LOGGER)
    handler = _Names(names, threading.get_ident())
    logger.addHandler(handler)
    try:
        yield names
    finally:
        logger.removeHandler(handler)


class _Names(logging.Handler):
    """A handler that keeps the names a record of one thread carries."""

    def __init__(self, names: list[str], thread: int) -> None:
        """Keep the list the names are added to, and whose they are.

        names -- the list
        thread -- the thread whose reports are kept
        """
        super().__init__()
        self.names = names
        self.thread = thread

    def emit(self, record: logging.LogRecord) -> None:
        """Add the names a report carries, if it is this thread's.

        record -- one report
        """
        if threading.get_ident() == self.thread:
            self.names.extend(getattr(record, _ATTRIBUTE, ()))
