"""Test text_spreadsheet._selection against the Data Model and CSVW."""

import unittest

from text_spreadsheet import _selection

A = {"sheet name": "A", "header": ["a", "b", "c"], "records": [["1", "2", "3"]]}
B = {"sheet name": "B", "header": None, "records": []}
C = {"sheet name": "C", "header": ["k"], "records": [["x"], ["y"], ["z"]]}
GROUP = [
    {"file": 1, "sheets": [A, B]},
    {"file": 2, "sheets": [C]},
]


def parts(selection):
    """Return the parts a selection names."""
    return _selection.values(selection)


def keep_y(records):
    """Keep the records whose first field is y."""
    return [n for n, record in enumerate(records, 1) if record[0] == "y"]


def keep_third_is_3(records):
    """Keep the records whose third field is 3."""
    return [n for n, record in enumerate(records, 1) if record[2] == "3"]


class TestSheets(unittest.TestCase):
    """of: which sheets a call names."""

    def test_all_of_them(self):
        """No address names every sheet of every file."""
        self.assertEqual(parts(_selection.of(GROUP)), [A, B, C])

    def test_numbered_across_the_group(self):
        """Sheets count from 1 across the files, and in each file."""
        self.assertEqual(
            [
                (entry["sheet"], entry["file"], entry["position in file"])
                for entry in _selection.of(GROUP)
            ],
            [(1, 1, 1), (2, 1, 2), (3, 2, 1)],
        )

    def test_one(self):
        """A position names one sheet of the group."""
        self.assertEqual(parts(_selection.of(GROUP, sheet="3")), [C])

    def test_the_order_written(self):
        """Sheets come back in the order the address writes them."""
        self.assertEqual(parts(_selection.of(GROUP, sheet="3;1")), [C, A])


class TestRecords(unittest.TestCase):
    """of: which records a call names."""

    def test_the_header_is_kept(self):
        """A sheet cut to one record is still a sheet."""
        self.assertEqual(
            parts(_selection.of(GROUP, sheet="3", rows="2")),
            [{"sheet name": "C", "header": ["k"], "records": [["y"]]}],
        )

    def test_a_record_that_does_not_exist(self):
        """A record that does not exist is left out, not refused."""
        part = parts(_selection.of(GROUP, sheet="3", rows="4"))[0]
        self.assertEqual(part["records"], [])

    def test_the_condition_comes_first(self):
        """rows counts the records the condition keeps."""
        selection = _selection.of(GROUP, sheet="3", rows="1", condition=keep_y)
        self.assertEqual(parts(selection)[0]["records"], [["y"]])

    def test_counts(self):
        """CSVW, 4.4: the records of the sheet, and those it keeps."""
        entry = _selection.of(GROUP, sheet="3", condition=keep_y)[0]
        self.assertEqual((entry["records"], entry["matches"]), (3, 1))

    def test_matches_without_a_condition(self):
        """With no condition, every record matches."""
        entry = _selection.of(GROUP, sheet="3")[0]
        self.assertEqual((entry["records"], entry["matches"]), (3, 3))


class TestFields(unittest.TestCase):
    """of: which fields a call names."""

    def test_the_header_is_cut_alike(self):
        """Header and records are cut by the same positions."""
        self.assertEqual(
            parts(_selection.of(GROUP, sheet="1", fields="1;3")),
            [{"sheet name": "A", "header": ["a", "c"], "records": [["1", "3"]]}],
        )

    def test_an_empty_sheet(self):
        """A sheet with no lines has no field, and stays empty."""
        self.assertEqual(parts(_selection.of(GROUP, sheet="2", fields="1")), [B])

    def test_the_condition_sees_the_whole_record(self):
        """fields cuts after the condition has seen every field."""
        selection = _selection.of(
            GROUP, sheet="1", fields="1", condition=keep_third_is_3
        )
        self.assertEqual(parts(selection)[0]["records"], [["1"]])
