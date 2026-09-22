"""Test text_spreadsheet._map against the draft's Data Model."""

import unittest
from pathlib import Path

import mtsv

from text_spreadsheet import _map

FF = chr(0x0C)
SOURCE = Path("/home/me/book.xlsx")
STORED = Path("/home/me/.cache/text-spreadsheet/home/me/book.xlsx.mtsv")
SHEETS = [
    {"sheet name": "People", "header": ["Name", "Age"], "records": [["Ada", "36"]]},
    {"sheet name": "Empty", "header": None, "records": []},
    {"sheet name": "Notes", "header": ["Key"], "records": [["a"], ["b"]]},
]


def named(value, name):
    """Return the sheet of that name in a map."""
    return next(sheet for sheet in value if sheet["sheet name"] == name)


class TestOf(unittest.TestCase):
    """of: what a file is made of."""

    def setUp(self):
        """Map the sheets above, as a call that converted them."""
        self.value = _map.of(SHEETS, SOURCE, STORED, True, ["cell type n"])

    def test_four_sheets(self):
        """The map holds file, sheets, columns and left behind."""
        self.assertEqual(
            [sheet["sheet name"] for sheet in self.value],
            ["file", "sheets", "columns", "left behind"],
        )

    def test_file(self):
        """The file sheet names the source, the copy and the call."""
        self.assertEqual(
            named(self.value, "file")["records"],
            [[str(SOURCE), str(STORED), "yes"]],
        )

    def test_file_not_converted(self):
        """A call served from the copy says so."""
        value = _map.of(SHEETS, SOURCE, STORED, False, [])
        self.assertEqual(named(value, "file")["records"][0][2], "no")

    def test_sheets(self):
        """Each sheet is numbered, named, counted, and given its lines."""
        self.assertEqual(
            named(self.value, "sheets")["records"],
            [
                ["1", "People", "1", "1", "3"],
                ["2", "Empty", "0", "4", "4"],
                ["3", "Notes", "2", "5", "8"],
            ],
        )

    def test_records_are_what_rows_addresses(self):
        """The count is the records, not the lines they occupy."""
        for record in named(self.value, "sheets")["records"]:
            with self.subTest(record[1]):
                sheet = SHEETS[int(record[0]) - 1]
                self.assertEqual(int(record[2]), len(sheet["records"]))

    def test_lines_match_the_generator(self):
        """Every first line is where the generator writes an FF."""
        lines = mtsv.dumps(SHEETS).split(chr(0x0A))
        for record in named(self.value, "sheets")["records"]:
            with self.subTest(record[1]):
                self.assertTrue(lines[int(record[3]) - 1].startswith(FF))

    def test_last_line_is_the_last(self):
        """The last sheet ends on the last line of the text."""
        lines = mtsv.dumps(SHEETS).split(chr(0x0A))
        last = named(self.value, "sheets")["records"][-1][4]
        self.assertEqual(int(last), len(lines) - 1)

    def test_columns(self):
        """Each column is given its sheet, position and name."""
        self.assertEqual(
            named(self.value, "columns")["records"],
            [
                ["1", "1", "Name"],
                ["1", "2", "Age"],
                ["3", "1", "Key"],
            ],
        )

    def test_left_behind(self):
        """What the conversion reported is carried as reported."""
        self.assertEqual(named(self.value, "left behind")["records"], [["cell type n"]])

    def test_nothing_left_behind(self):
        """A conversion that lost nothing carries no rows."""
        value = _map.of(SHEETS, SOURCE, STORED, True, [])
        self.assertEqual(named(value, "left behind")["records"], [])

    def test_the_map_is_mtsv(self):
        """The map is itself a file the generator can write."""
        self.assertEqual(mtsv.loads(mtsv.dumps(self.value)), self.value)
