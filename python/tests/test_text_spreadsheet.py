"""Test text_spreadsheet.read: map, values, filter and folder."""

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
WIDE = [
    {
        "sheet name": "W",
        "header": ["a", "b"],
        "records": [["1", "2"], ["3", "4"], ["5", "2"]],
    }
]


def named(text, name):
    """Return the sheet of that name in a map."""
    return next(sheet for sheet in mtsv.loads(text) if sheet["sheet name"] == name)


class Folder(unittest.TestCase):
    """A temporary folder, and the copies a test leaves in the cache."""

    def setUp(self):
        """Make the folder."""
        self.directory = tempfile.TemporaryDirectory()
        self.folder = Path(self.directory.name)

    def tearDown(self):
        """Remove the folder and the copies made from it."""
        shutil.rmtree(_cache.artifact(self.folder / "x").parent, ignore_errors=True)
        self.directory.cleanup()

    def write(self, name, value=SHEETS):
        """Write sheets to a file in the folder, and return its path."""
        path = self.folder / name
        with path.open("wb") as fp:
            if path.suffix == ".mtsv":
                mtsv.dump(value, fp)
            else:
                xlsx.dump(value, fp)
        return path


class TestMap(Folder):
    """read: the map of a file."""

    def test_maps_a_spreadsheet(self):
        """The map names each sheet of the file."""
        path = self.write("book.xlsx")
        records = named(read(str(path)), "sheets")["records"]
        self.assertEqual([record[2] for record in records], ["People"])

    def test_names_the_file_and_the_copy(self):
        """The file sheet names the source and the copy."""
        path = self.write("book.xlsx")
        record = named(read(str(path)), "file")["records"][0]
        self.assertEqual(record[1:4], [str(path), str(_cache.artifact(path)), "yes"])

    def test_serves_the_copy(self):
        """A file no newer than its copy is not converted again."""
        path = self.write("book.xlsx")
        read(str(path))
        with _cache.artifact(path).open("wb") as fp:
            mtsv.dump(OTHER, fp)
        text = read(str(path))
        self.assertEqual(named(text, "file")["records"][0][3], "no")
        self.assertEqual(named(text, "sheets")["records"][0][2], "Other")

    def test_converts_again_when_the_file_changes(self):
        """A file newer than its copy is converted again."""
        path = self.write("book.xlsx")
        read(str(path))
        os.utime(_cache.artifact(path), (0, 0))
        self.assertEqual(named(read(str(path)), "file")["records"][0][3], "yes")

    def test_a_filter_shapes_the_map(self):
        """With a filter and no position, the map counts matches."""
        path = self.write("book.xlsx", WIDE)
        record = named(read(str(path), filter="@[1] == '2'"), "sheets")["records"][0]
        self.assertEqual(record[3:5], ["3", "2"])

    def test_extension_must_name_a_format(self):
        """A file named directly with no extension names no format."""
        path = self.folder / "book"
        path.write_bytes(b"a\n")
        with self.assertRaises(LookupError):
            read(str(path))

    def test_relative_path_refused(self):
        """A path that is not absolute raises ValueError."""
        with self.assertRaises(ValueError):
            read("book.xlsx")


class TestValues(Folder):
    """read: the part of a file an address names."""

    def test_one_sheet(self):
        """An address names a sheet, and no map comes back."""
        path = self.write("book.xlsx")
        self.assertEqual(mtsv.loads(read(str(path), sheet="1")), SHEETS)

    def test_records_and_fields(self):
        """Records and fields are cut, and the header is kept."""
        path = self.write("book.xlsx", WIDE)
        self.assertEqual(
            mtsv.loads(read(str(path), sheet="1", rows="1", fields="2")),
            [{"sheet name": "W", "header": ["b"], "records": [["2"]]}],
        )

    def test_rows_page_the_matches(self):
        """rows counts the records the filter keeps."""
        path = self.write("book.xlsx", WIDE)
        text = read(str(path), sheet="1", rows="2", filter="@[1] == '2'")
        self.assertEqual(mtsv.loads(text)[0]["records"], [["5", "2"]])

    def test_fields_past_the_width(self):
        """A sheet left with no field comes back empty, as MTSV."""
        path = self.write("book.xlsx")
        self.assertEqual(
            mtsv.loads(read(str(path), sheet="1", fields="2")),
            [{"sheet name": "People", "header": None, "records": []}],
        )

    def test_a_sheet_that_does_not_exist(self):
        """A sheet the file does not have is left out."""
        path = self.write("book.xlsx")
        self.assertEqual(mtsv.loads(read(str(path), sheet="2")), [])

    def test_a_filter_refused(self):
        """A filter not written as RFC 9535 writes one is refused."""
        path = self.write("book.xlsx")
        with self.assertRaises(ValueError):
            read(str(path), filter="@[0] = 'x'")


class TestFolder(Folder):
    """read: a folder of files."""

    def test_every_file_in_one_map(self):
        """The map lists every file and every sheet, numbered across."""
        self.write("a.mtsv")
        self.write("b.xlsx", OTHER)
        text = read(str(self.folder))
        self.assertEqual(len(named(text, "file")["records"]), 2)
        self.assertEqual(
            [record[:3] for record in named(text, "sheets")["records"]],
            [["1", "1", "People"], ["2", "2", "Other"]],
        )

    def test_a_sheet_across_the_group(self):
        """sheet counts across the files."""
        self.write("a.mtsv")
        self.write("b.mtsv", OTHER)
        self.assertEqual(mtsv.loads(read(str(self.folder), sheet="2")), OTHER)

    def test_fields_across_widths(self):
        """Each sheet of the group keeps the fields it has."""
        self.write("a.mtsv", WIDE)
        self.write("b.mtsv")
        text = read(str(self.folder), fields="2")
        self.assertEqual([sheet["header"] for sheet in mtsv.loads(text)], [["b"], None])

    def test_a_folder_of_folders(self):
        """A folder holding only subfolders names them as skipped."""
        (self.folder / "2026").mkdir()
        record = named(read(str(self.folder)), "file")["records"][0]
        self.assertEqual((record[0], record[4]), ("1", "skipped: subfolder"))

    def test_an_empty_folder(self):
        """A folder with no sheets still returns its map."""
        self.assertEqual(named(read(str(self.folder)), "sheets")["records"], [])
