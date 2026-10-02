"""Test text_spreadsheet._conversion: in place, kept, converted.

Classes:
TestOf -- of: the sheets of a file, and what its conversion left
TestRefused -- of: a file that cannot be read or converted
"""

__all__ = ["TestOf", "TestRefused"]

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import mtsv
from mtsv.integrations import xlsx

from text_spreadsheet import _cache, _conversion, _refusal

import support

SHEETS = [{"sheet name": "People", "header": ["Name"], "records": [["Ada"]]}]
LEAVES_BEHIND = b'[{"sheet name":"","header":["a"],"records":[],"x":1}]'
LEAVES_A_TAB = b'[{"sheet name":"","header":["a"],"records":[],"x\\ty":1}]'
HOLDS_A_LINE_BREAK = b'[{"sheet name":"","header":["a"],"records":[["b\\nc"]]}]'


class Directory(unittest.TestCase):
    """A temporary directory, and the copies its tests leave."""

    def setUp(self):
        """Make the directory."""
        self.temporary = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary.name)

    def tearDown(self):
        """Remove the directory and the copies made from it."""
        copies = _cache.location(self.directory / "x").parent
        shutil.rmtree(copies, ignore_errors=True)
        self.temporary.cleanup()

    def write(self, name, value=SHEETS):
        """Write sheets, or bytes, to a file in the directory."""
        pathname = self.directory / name
        with pathname.open("wb") as fp:
            if isinstance(value, bytes):
                fp.write(value)
            elif pathname.suffix == ".mtsv":
                mtsv.dump(value, fp)
            else:
                xlsx.dump(value, fp)
        return pathname


class TestOf(Directory):
    """of: the sheets of a file, and what its conversion left."""

    def test_mtsv_read_in_place(self):
        """An MTSV file is read where it is, and no copy is made."""
        pathname = self.write("book.mtsv")
        converted = _conversion.of(pathname)
        self.assertEqual((converted["left behind"], converted["sheets"]), ([], SHEETS))
        self.assertFalse(_cache.location(pathname).exists())

    def test_converted_then_kept(self):
        """A first call converts; a second reads the copy."""
        pathname = self.write("book.xlsx")
        _conversion.of(pathname)
        self.assertTrue(_cache.location(pathname).exists())
        with mock.patch("text_spreadsheet._conversion._loaded") as loaded:
            self.assertEqual(_conversion.of(pathname)["sheets"], SHEETS)
        loaded.assert_not_called()

    def test_left_behind_survives_the_copy(self):
        """What a conversion left behind is read back with the copy."""
        pathname = self.write("book.json", LEAVES_BEHIND)
        self.assertEqual(_conversion.of(pathname)["left behind"], ["x"])
        self.assertEqual(_conversion.of(pathname)["left behind"], ["x"])

    def test_a_loss_no_field_holds(self):
        """A loss named with a tab is kept as a field holds it."""
        pathname = self.write("book.json", LEAVES_A_TAB)
        self.assertEqual(_conversion.of(pathname)["left behind"], ["x�y"])
        self.assertEqual(_conversion.of(pathname)["left behind"], ["x�y"])

    def test_a_damaged_copy_is_made_again(self):
        """A copy whose metadata cannot be read is converted again."""
        pathname = self.write("book.xlsx")
        _conversion.of(pathname)
        stored = _cache.location(pathname)
        stored.with_name(stored.name + "-metadata.mtsv").write_bytes(b"x\n")
        self.assertEqual(_conversion.of(pathname)["sheets"], SHEETS)
        self.assertEqual(_cache.load(stored)[1], [])

    def test_a_copy_that_cannot_be_written(self):
        """XDG, Basics: the read goes on, and no copy is kept."""
        pathname = self.write("book.xlsx")
        with mock.patch("text_spreadsheet._cache.store", side_effect=OSError("full")):
            converted = _conversion.of(pathname)
        self.assertEqual(converted["sheets"], SHEETS)
        self.assertFalse(_cache.location(pathname).exists())


class TestRefused(Directory):
    """of: a file that cannot be read or converted."""

    def test_no_format(self):
        """An extension that names no format, as LookupError."""
        with self.assertRaises(_refusal.LookupRefusalError):
            _conversion.of(self.write("book.txt", b"a\n"))

    def test_absent(self):
        """A file that does not exist, as OSError."""
        for name in ("absent.xlsx", "absent.mtsv"):
            with self.subTest(name):
                with self.assertRaises(_refusal.OSRefusalError):
                    _conversion.of(self.directory / name)

    def test_a_pathname_that_names_no_file(self):
        """A pathname holding a null character, as ValueError."""
        for name in ("a\0b.xlsx", "a\0b.mtsv"):
            with self.subTest(name):
                with self.assertRaises(_refusal.ValueRefusalError):
                    _conversion.of(self.directory / name)

    def test_not_mtsv(self):
        """An MTSV file that is not MTSV, as ValueError."""
        with self.assertRaises(_refusal.ValueRefusalError):
            _conversion.of(self.write("book.mtsv", b"a\tb\nc\n"))

    def test_a_value_mtsv_cannot_hold(self):
        """mtsv, What is left behind: a line break in a value raises."""
        with self.assertRaises(_refusal.ValueRefusalError):
            _conversion.of(self.write("book.json", HOLDS_A_LINE_BREAK))
