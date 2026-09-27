"""Test text_spreadsheet._map against the draft and CSVW."""

import unittest
from pathlib import Path

import mtsv

from text_spreadsheet import _map, _selection

SHEETS = [
    {"sheet name": "People", "header": ["Name", "Age"], "records": [["Ada", "36"]]},
    {"sheet name": "Empty", "header": None, "records": []},
]
NOTES = [{"sheet name": "Notes", "header": ["Key"], "records": [["a"], ["b"]]}]
GROUP = [
    {
        "file": 1,
        "source": Path("/home/me/book.xlsx"),
        "status": "read",
        "artifact": Path("/home/me/.cache/text-spreadsheet/home/me/book.xlsx.mtsv"),
        "converted": True,
        "left behind": ["cell type n", "x�y"],
        "text": mtsv.dumps(SHEETS),
        "sheets": SHEETS,
    },
    {
        "file": 2,
        "source": Path("/home/me/notes.mtsv"),
        "status": "read",
        "artifact": Path("/home/me/notes.mtsv"),
        "converted": False,
        "left behind": [],
        "text": mtsv.dumps(NOTES),
        "sheets": NOTES,
    },
    {
        "file": 3,
        "source": Path("/home/me/a\tb.csv"),
        "status": "failed: name cannot be written",
        "artifact": None,
        "converted": False,
        "left behind": [],
        "text": "",
        "sheets": [],
    },
]


def named(value, name):
    """Return the sheet of that name in a map."""
    return next(sheet for sheet in value if sheet["sheet name"] == name)


class TestOf(unittest.TestCase):
    """of: what a group of files is made of."""

    def setUp(self):
        """Map the whole group."""
        self.value = _map.of(GROUP, _selection.of(GROUP))

    def test_four_sheets(self):
        """The map holds file, sheets, columns and left behind."""
        self.assertEqual(
            [sheet["sheet name"] for sheet in self.value],
            ["file", "sheets", "columns", "left behind"],
        )

    def test_file(self):
        """Each file: position, source, artifact, converted, status."""
        self.assertEqual(
            named(self.value, "file")["records"],
            [
                [
                    "1",
                    "/home/me/book.xlsx",
                    "/home/me/.cache/text-spreadsheet/home/me/book.xlsx.mtsv",
                    "yes",
                    "read",
                ],
                ["2", "/home/me/notes.mtsv", "/home/me/notes.mtsv", "no", "read"],
                [
                    "3",
                    "/home/me/a�b.csv",
                    "",
                    "no",
                    "failed: name cannot be written",
                ],
            ],
        )

    def test_sheets(self):
        """Each sheet: group position, file, name, counts and lines."""
        self.assertEqual(
            named(self.value, "sheets")["records"],
            [
                ["1", "1", "People", "1", "1", "1", "3"],
                ["2", "1", "Empty", "0", "0", "4", "4"],
                ["3", "2", "Notes", "2", "2", "1", "4"],
            ],
        )

    def test_lines_follow_the_selection(self):
        """A sheet chosen alone keeps its own lines in its file."""
        value = _map.of(GROUP, _selection.of(GROUP, sheet="3"))
        self.assertEqual(
            named(value, "sheets")["records"],
            [["3", "2", "Notes", "2", "2", "1", "4"]],
        )

    def test_columns(self):
        """Each column is given its sheet, position and name."""
        self.assertEqual(
            named(self.value, "columns")["records"],
            [["1", "1", "Name"], ["1", "2", "Age"], ["3", "1", "Key"]],
        )

    def test_left_behind(self):
        """Each loss is named with its file."""
        self.assertEqual(
            named(self.value, "left behind")["records"],
            [["1", "cell type n"], ["1", "x�y"]],
        )

    def test_the_map_is_mtsv(self):
        """The map is itself a file the generator can write."""
        self.assertEqual(mtsv.loads(mtsv.dumps(self.value)), self.value)


class TestLines(unittest.TestCase):
    """of: where each sheet's lines are in its file's text."""

    def lines(self, text, sheets):
        """Return the first and last lines the map gives each sheet."""
        group = [
            {
                "file": 1,
                "source": Path("/a.mtsv"),
                "status": "read",
                "artifact": Path("/a.mtsv"),
                "converted": False,
                "left behind": [],
                "text": text,
                "sheets": sheets,
            }
        ]
        records = named(_map.of(group, _selection.of(group)), "sheets")["records"]
        return [(record[5], record[6]) for record in records]

    def test_written_by_the_generator(self):
        """Every sheet begins at its FF line."""
        sheets = SHEETS + NOTES
        self.assertEqual(
            self.lines(mtsv.dumps(sheets), sheets), [("1", "3"), ("4", "4"), ("5", "8")]
        )

    def test_a_first_sheet_without_an_ff_line(self):
        """The draft, Parsers: lines before the first FF are a sheet."""
        text = "a\nb\n\fNext\nc\n"
        self.assertEqual(self.lines(text, mtsv.loads(text)), [("1", "2"), ("3", "4")])

    def test_an_encoding_signature(self):
        """The draft, Parsers: a U+FEFF at the start is not a line."""
        text = "﻿\fA\nk\n"
        self.assertEqual(self.lines(text, mtsv.loads(text)), [("1", "2")])
