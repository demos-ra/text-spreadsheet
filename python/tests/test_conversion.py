"""Test text_spreadsheet._conversion: in place, stored, converted."""

import shutil
import tempfile
import unittest
from pathlib import Path

import mtsv
from mtsv.integrations import xlsx

from text_spreadsheet import _cache, _conversion

import support

SHEETS = [{"sheet name": "People", "header": ["Name"], "records": [["Ada"]]}]
LEAVES_BEHIND = b'[{"sheet name":"","header":["a"],"records":[],"x":1}]'
LEAVES_A_TAB = b'[{"sheet name":"","header":["a"],"records":[],"x\\ty":1}]'


class Folder(unittest.TestCase):
    """A temporary folder, and the copies a test leaves in the cache."""

    def setUp(self):
        """Make the folder."""
        self.directory = tempfile.TemporaryDirectory()
        self.folder = Path(self.directory.name)

    def tearDown(self):
        """Remove the folder and the copies made from it."""
        cache = _cache.artifact(self.folder / "x").parent
        shutil.rmtree(cache, ignore_errors=True)
        self.directory.cleanup()

    def write(self, name, value=SHEETS):
        """Write sheets, or bytes, to a file in the folder."""
        path = self.folder / name
        with path.open("wb") as fp:
            if isinstance(value, bytes):
                fp.write(value)
            elif path.suffix == ".mtsv":
                mtsv.dump(value, fp)
            else:
                xlsx.dump(value, fp)
        return path


class TestOf(Folder):
    """of: the MTSV text of a file, and what its conversion left."""

    def test_mtsv_read_in_place(self):
        """An MTSV file is its own artifact, and no copy is made."""
        path = self.write("book.mtsv")
        converted = _conversion.of(path)
        self.assertEqual((converted["artifact"], converted["converted"]), (path, False))
        self.assertEqual(converted["sheets"], SHEETS)
        self.assertFalse(_cache.artifact(path).exists())

    def test_converted_then_stored(self):
        """A first call converts; a second reads the copy."""
        path = self.write("book.xlsx")
        first = _conversion.of(path)
        second = _conversion.of(path)
        self.assertEqual((first["converted"], second["converted"]), (True, False))
        self.assertEqual(second["sheets"], SHEETS)

    def test_left_behind_survives_the_copy(self):
        """What a conversion left behind is read back with the copy."""
        path = self.write("book.json", LEAVES_BEHIND)
        self.assertEqual(_conversion.of(path)["left behind"], ["x"])
        self.assertEqual(_conversion.of(path)["left behind"], ["x"])

    def test_a_loss_no_field_holds(self):
        """A loss named with a tab is kept as a field holds it."""
        path = self.write("book.json", LEAVES_A_TAB)
        self.assertEqual(_conversion.of(path)["left behind"], ["x�y"])
        self.assertEqual(_conversion.of(path)["left behind"], ["x�y"])

    def test_a_damaged_copy_is_made_again(self):
        """A copy whose metadata cannot be read is converted again."""
        path = self.write("book.xlsx")
        _conversion.of(path)
        stored = _cache.artifact(path)
        stored.with_name(stored.name + "-metadata.mtsv").write_bytes(b"x\n")
        again = _conversion.of(path)
        self.assertEqual((again["converted"], again["sheets"]), (True, SHEETS))

    def test_no_format(self):
        """An extension that names no format raises LookupError."""
        with self.assertRaises(LookupError):
            _conversion.of(self.write("book.txt", b"a\n"))

    def test_not_mtsv(self):
        """An MTSV file that is not MTSV raises ValueError."""
        with self.assertRaises(ValueError):
            _conversion.of(self.write("book.mtsv", b"a\tb\nc\n"))
