"""Shared setup for the tests: the logger, and the cache directory.

Objects:
CACHE -- the cache directory of the test run, a temporary directory
user_cache_dir -- platformdirs' user_cache_dir as the tests patch it,
    returning CACHE
"""

__all__ = ["CACHE", "user_cache_dir"]

import atexit
import logging
import tempfile
from pathlib import Path
from unittest import mock

# mtsv reports what is left behind on this logger. A NullHandler takes
# the reports of a test run, and they go no further.
_LOGGER = logging.getLogger("mtsv")
_LOGGER.addHandler(logging.NullHandler())
_LOGGER.propagate = False

_DIRECTORY = tempfile.TemporaryDirectory()
atexit.register(_DIRECTORY.cleanup)
CACHE = Path(_DIRECTORY.name)
user_cache_dir = mock.patch(
    "text_spreadsheet._cache.user_cache_dir", return_value=_DIRECTORY.name
).start()
