"""Shared setup for the tests: the logger, and the cache directory.

Objects:
CACHE -- the cache directory of the test run, a temporary folder
user_cache_dir -- platformdirs' user_cache_dir as the tests patch it,
    returning CACHE
"""

import atexit
import logging
import tempfile
from pathlib import Path
from unittest import mock

# Logging HOWTO, Configuring Logging for a Library: a library adds a
# NullHandler where its events should not be printed without
# configuration.
_LOGGER = logging.getLogger("mtsv")
_LOGGER.addHandler(logging.NullHandler())
_LOGGER.propagate = False

_FOLDER = tempfile.TemporaryDirectory()
atexit.register(_FOLDER.cleanup)
CACHE = Path(_FOLDER.name)
user_cache_dir = mock.patch(
    "text_spreadsheet._cache.user_cache_dir", return_value=_FOLDER.name
).start()
