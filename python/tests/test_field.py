"""Test text_spreadsheet._field against the draft's Generators.

Classes:
TestHolds -- holds: whether a field can hold a text
TestWritten -- written: a text as a field holds it
"""

__all__ = ["TestHolds", "TestWritten"]

import unittest

from text_spreadsheet import _field


class TestHolds(unittest.TestCase):
    """holds: whether a field can hold a text."""

    def test_text(self):
        """Text without HTAB, LF, FF or CR is held."""
        self.assertTrue(_field.holds("a b\u000b\u0000é"))

    def test_the_separators(self):
        """HTAB, LF, FF and CR are not."""
        for char in "\t\n\f\r":
            with self.subTest(repr(char)):
                self.assertFalse(_field.holds(f"a{char}b"))


class TestWritten(unittest.TestCase):
    """written: a text as a field holds it."""

    def test_unchanged(self):
        """Text a field holds is written as it is."""
        self.assertEqual(_field.written("a b"), "a b")

    def test_replaced(self):
        """Each HTAB, LF, FF and CR is written as U+FFFD."""
        self.assertEqual(_field.written("a\tb\nc\fd\re"), "a�b�c�d�e")
