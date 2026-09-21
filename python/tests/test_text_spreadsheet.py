"""Test text_spreadsheet.read against the formats and the cache."""

import os
import shutil
import tempfile
import unittest
from pathlib import Path

import mtsv
from mtsv.integrations import xlsx

from text_spreadsheet import _cache, read

import support

SHEETS = [{"sheet name": "People", "header": ["Name"], "records": [["Ada"]]}]
OTHER = [{"sheet name": "Other", "header": ["Name"], "records": [["Bo"]]}]
WIDE = [{"sheet name": "W", "header": ["a", "b"], "records": [["1", "2"]]}]
LEAVES_BEHIND = b'[{"sheet name":"","header":["a"],"records":[],"x":1}]'


def written(directory, name, value=SHEETS):
    """Write sheets to a file in a directory, and return its path."""
    path = Path(directory, name)
    with path.open("wb") as fp:
        if path.suffix == ".mtsv":
            mtsv.dump(value, fp)
        else:
            xlsx.dump(value, fp)
    return path


def named(text, name):
    """Return the sheet of that name in a map."""
    return next(sheet for sheet in mtsv.loads(text) if sheet["sheet name"] == name)


class TestRead(unittest.TestCase):
    """read: the map of the file at a path."""

    def setUp(self):
        """Collect the copies to remove."""
        self.stored = []

    def tearDown(self):
        """Remove the copies the test left in the cache."""
        for path in self.stored:
            shutil.rmtree(path.parent, ignore_errors=True)

    def note(self, path):
        """Note where the copy of a file goes, and return the path."""
        self.stored.append(_cache.artifact(path))
        return path

    def test_maps_a_spreadsheet(self):
        """The map names each sheet of the file."""
        with tempfile.TemporaryDirectory() as directory:
            path = self.note(written(directory, "book.xlsx"))
            records = named(read(str(path)), "sheets")["records"]
            self.assertEqual([record[1] for record in records], ["People"])

    def test_maps_the_columns(self):
        """The map gives each column its sheet and position."""
        with tempfile.TemporaryDirectory() as directory:
            path = self.note(written(directory, "book.xlsx"))
            records = named(read(str(path)), "columns")["records"]
            self.assertEqual(records, [["1", "1", "Name"]])

    def test_names_the_file_and_the_copy(self):
        """The file sheet names the source and the copy."""
        with tempfile.TemporaryDirectory() as directory:
            path = self.note(written(directory, "book.xlsx"))
            record = named(read(str(path)), "file")["records"][0]
            self.assertEqual(record[0], str(path))
            self.assertEqual(record[1], str(_cache.artifact(path)))

    def test_keeps_a_copy(self):
        """The copy holds the file as MTSV, not the map."""
        with tempfile.TemporaryDirectory() as directory:
            path = self.note(written(directory, "book.xlsx"))
            read(str(path))
            with _cache.artifact(path).open("rb") as fp:
                self.assertEqual(mtsv.load(fp), SHEETS)

    def test_serves_the_copy(self):
        """A file no newer than its copy is not converted again."""
        with tempfile.TemporaryDirectory() as directory:
            path = self.note(written(directory, "book.xlsx"))
            read(str(path))
            stored = _cache.artifact(path)
            with stored.open("wb") as fp:
                mtsv.dump(OTHER, fp)
            text = read(str(path))
            self.assertEqual(named(text, "file")["records"][0][2], "no")
            records = named(text, "sheets")["records"]
            self.assertEqual([record[1] for record in records], ["Other"])

    def test_converts_again_when_the_file_changes(self):
        """A file newer than its copy is converted again."""
        with tempfile.TemporaryDirectory() as directory:
            path = self.note(written(directory, "book.xlsx"))
            read(str(path))
            os.utime(_cache.artifact(path), (0, 0))
            text = read(str(path))
            self.assertEqual(named(text, "file")["records"][0][2], "yes")

    def test_carries_what_was_left_behind(self):
        """What the integration reported is carried as reported."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "book.json")
            path.write_bytes(LEAVES_BEHIND)
            self.note(path)
            records = named(read(str(path)), "left behind")["records"]
            self.assertEqual(records, [["x"]])

    def test_nothing_left_behind(self):
        """A conversion that lost nothing carries no rows."""
        with tempfile.TemporaryDirectory() as directory:
            path = self.note(written(directory, "book.mtsv"))
            records = named(read(str(path)), "left behind")["records"]
            self.assertEqual(records, [])

    def test_extension_must_name_a_format(self):
        """A name with no extension names no format, so it stops.

        Every format is named by the extension its media type
        registration declares, so a name that carries no extension
        can never name one.
        """
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "book")
            path.write_bytes(b"a\n")
            self.note(path)
            with self.assertRaises(LookupError):
                read(str(path))

    def test_relative_path_refused(self):
        """A path that is not absolute raises ValueError."""
        with self.assertRaises(ValueError):
            read("book.xlsx")

    def test_one_sheet(self):
        """An address names a sheet, and no map comes back."""
        with tempfile.TemporaryDirectory() as directory:
            path = self.note(written(directory, "book.xlsx"))
            self.assertEqual(mtsv.loads(read(str(path), sheet="1")), SHEETS)

    def test_records_and_fields(self):
        """Records and fields are cut, and the header is kept."""
        with tempfile.TemporaryDirectory() as directory:
            path = self.note(written(directory, "book.xlsx", WIDE))
            text = read(str(path), sheet="1", rows="1", fields="2")
            self.assertEqual(
                mtsv.loads(text),
                [{"sheet name": "W", "header": ["b"], "records": [["2"]]}],
            )

    def test_an_address_past_the_end(self):
        """A sheet the file does not have is refused."""
        with tempfile.TemporaryDirectory() as directory:
            path = self.note(written(directory, "book.xlsx"))
            with self.assertRaises(ValueError):
                read(str(path), sheet="2")
