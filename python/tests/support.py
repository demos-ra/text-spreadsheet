"""Shared setup for the tests: the logger an integration reports on."""

import logging

# Logging HOWTO, Configuring Logging for a Library: a library adds a
# NullHandler where its events should not be printed without
# configuration.
_LOGGER = logging.getLogger("mtsv")
_LOGGER.addHandler(logging.NullHandler())
_LOGGER.propagate = False
