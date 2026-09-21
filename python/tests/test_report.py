"""Test text_spreadsheet._report against mtsv's left-behind report."""

import logging
import unittest

from text_spreadsheet import _report

import support

LOGGER = "mtsv.integrations"


class TestCollect(unittest.TestCase):
    """collect: the names an integration reported as left behind."""

    def test_collects_the_names(self):
        """The names a record carries are collected, in order."""
        with _report.collect() as names:
            logging.getLogger(LOGGER).warning(
                "left behind: a, b", extra={"left_behind": ["a", "b"]}
            )
        self.assertEqual(names, ["a", "b"])

    def test_two_reports(self):
        """More than one report adds to the same list."""
        logger = logging.getLogger(LOGGER)
        with _report.collect() as names:
            logger.warning("x", extra={"left_behind": ["a"]})
            logger.warning("y", extra={"left_behind": ["b"]})
        self.assertEqual(names, ["a", "b"])

    def test_nothing_reported(self):
        """A body that reports nothing collects nothing."""
        with _report.collect() as names:
            pass
        self.assertEqual(names, [])

    def test_a_warning_without_names(self):
        """A record with no names of its own adds none."""
        with _report.collect() as names:
            logging.getLogger(LOGGER).warning("something else")
        self.assertEqual(names, [])

    def test_the_handler_is_removed(self):
        """The logger is left as it was found."""
        logger = logging.getLogger(LOGGER)
        before = list(logger.handlers)
        with _report.collect():
            self.assertEqual(len(logger.handlers), len(before) + 1)
        self.assertEqual(logger.handlers, before)

    def test_removed_after_an_error(self):
        """A body that raises still leaves the logger as found."""
        logger = logging.getLogger(LOGGER)
        before = list(logger.handlers)
        with self.assertRaises(ValueError):
            with _report.collect():
                raise ValueError
        self.assertEqual(logger.handlers, before)
