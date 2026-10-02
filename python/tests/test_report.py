"""Test text_spreadsheet._report against POSIX and CSVW.

Classes:
TestOf -- of: what every reply states of its files and sheets
"""

__all__ = ["TestOf"]

import unittest
from pathlib import Path

import mtsv

from text_spreadsheet import _report, _selection

SHEETS = [
    {"sheet name": "People", "header": ["Name"], "records": [["Ada"], ["Bo"]]},
    {"sheet name": "Empty", "header": None, "records": []},
]
GROUP = [
    {
        "file": 1,
        "source": Path("/home/me/book.xlsx"),
        "not read": None,
        "left behind": ["cell type n", "x�y"],
        "sheets": SHEETS,
    },
    {
        "file": 2,
        "source": Path("/home/me/a\tb.txt"),
        "not read": "no format",
        "left behind": [],
        "sheets": [],
    },
    {
        "file": 3,
        "source": Path("/home/me/2026"),
        "not read": "skipped: directory",
        "left behind": [],
        "sheets": [],
    },
]


def keep_bo(records):
    """Keep the records whose first field is Bo."""
    return [n for n, record in enumerate(records, 1) if record[0] == "Bo"]


class TestOf(unittest.TestCase):
    """of: what every reply states of its files and sheets."""

    def setUp(self):
        """Report the whole group, with nothing selected."""
        self.value = _report.of(GROUP, _selection.of(GROUP))
        self.file, self.not_read, self.left_behind, self.sheets = self.value

    def test_four_sheets_from_big_to_small(self):
        """The report: file, not read, left behind, then sheets."""
        self.assertEqual(
            [sheet["sheet name"] for sheet in self.value],
            ["file", "not read", "left behind", "sheets"],
        )

    def test_file(self):
        """Each file, read or not: its position and its source."""
        self.assertEqual(self.file["header"], ["file", "source"])
        self.assertEqual(
            self.file["records"],
            [
                ["1", "/home/me/book.xlsx"],
                ["2", "/home/me/a�b.txt"],
                ["3", "/home/me/2026"],
            ],
        )

    def test_not_read(self):
        """Each file not read: its position and its status."""
        self.assertEqual(self.not_read["header"], ["file", "status"])
        self.assertEqual(
            self.not_read["records"],
            [["2", "no format"], ["3", "skipped: directory"]],
        )

    def test_left_behind(self):
        """Each loss is named with its file."""
        self.assertEqual(self.left_behind["header"], ["file", "what"])
        self.assertEqual(
            self.left_behind["records"], [["1", "cell type n"], ["1", "x�y"]]
        )

    def test_sheets(self):
        """Each sheet: its file, its position there, name and counts."""
        self.assertEqual(
            self.sheets["header"],
            ["file", "sheet", "sheet name", "records", "matches", "positions"],
        )
        self.assertEqual(
            self.sheets["records"],
            [["1", "1", "People", "2", "2", "1-2"], ["1", "2", "Empty", "0", "0", ""]],
        )

    def test_sheets_follow_the_selection(self):
        """Counts are the sheet's; positions names what was named."""
        selection = _selection.of(GROUP, sheet="1", records="1", condition=keep_bo)
        self.assertEqual(
            _report.of(GROUP, selection)[3]["records"],
            [["1", "1", "People", "2", "1", "2"]],
        )

    def test_nothing_to_state(self):
        """With nothing to state, each sheet comes with no record."""
        value = _report.of([], [])
        self.assertEqual(len(value), 4)
        self.assertEqual([sheet["records"] for sheet in value], [[], [], [], []])

    def test_the_report_is_mtsv(self):
        """The report is itself a file the generator can write."""
        self.assertEqual(mtsv.loads(mtsv.dumps(self.value)), self.value)
