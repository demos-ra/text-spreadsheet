"""Test text_spreadsheet._refusal: a refusal, of each kind."""

import unittest

from text_spreadsheet import _refusal


class TestKinds(unittest.TestCase):
    """The refusals: each a refusal, and of its standard kind."""

    def test_each_is_a_refusal_of_its_kind(self):
        """A refusal is caught as one, and as the kind it keeps."""
        kinds = (
            (_refusal.ValueRefusalError, ValueError),
            (_refusal.LookupRefusalError, LookupError),
            (_refusal.OSRefusalError, OSError),
        )
        for refusal, kind in kinds:
            with self.subTest(refusal.__name__):
                error = refusal("why")
                self.assertIsInstance(error, _refusal.RefusalError)
                self.assertIsInstance(error, kind)
                self.assertEqual(str(error), "why")


class TestOf(unittest.TestCase):
    """of: the refusal an error of what a call names is."""

    def test_the_kind_is_kept(self):
        """Each standard kind becomes the refusal of that kind."""
        errors = (
            (ValueError("v"), _refusal.ValueRefusalError),
            (
                UnicodeDecodeError("utf-8", b"\xff", 0, 1, "u"),
                _refusal.ValueRefusalError,
            ),
            (LookupError("l"), _refusal.LookupRefusalError),
            (
                FileNotFoundError(2, "No such file or directory", "/a"),
                _refusal.OSRefusalError,
            ),
        )
        for error, refusal in errors:
            with self.subTest(type(error).__name__):
                self.assertIsInstance(_refusal.of(error), refusal)

    def test_the_reason_is_kept(self):
        """The refusal carries the error's message."""
        error = FileNotFoundError(2, "No such file or directory", "/a")
        self.assertEqual(str(_refusal.of(error)), str(error))
