"""Test text_spreadsheet._selection against the Data Model and CSVW.

Classes:
TestSheets -- of: which sheets a call names
TestRecords -- of: which records a call names
TestFields -- of: which fields a call names
TestRefused -- of: a selection not written as the syntax writes one
"""

__all__ = ["TestSheets", "TestRecords", "TestFields", "TestRefused"]

import unittest

from text_spreadsheet import _refusal, _selection

A = {"sheet name": "A", "header": ["a", "b", "c"], "records": [["1", "2", "3"]]}
B = {"sheet name": "B", "header": None, "records": []}
C = {"sheet name": "C", "header": ["k"], "records": [["x"], ["y"], ["z"]]}
FIRST = {"file": 1, "sheets": [A, B]}
SECOND = {"file": 2, "sheets": [C]}
GROUP = [FIRST, SECOND]


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
        """No selection names every sheet of every file."""
        self.assertEqual(parts(_selection.of(GROUP)), [A, B, C])

    def test_numbered_in_each_file(self):
        """The draft, Data Model: sheets count from 1 in their file."""
        self.assertEqual(
            [(entry["file"], entry["sheet"]) for entry in _selection.of(GROUP)],
            [(1, 1), (1, 2), (2, 1)],
        )

    def test_the_same_position_in_every_file(self):
        """A position names that sheet of each file."""
        self.assertEqual(parts(_selection.of(GROUP, sheet="1")), [A, C])

    def test_a_sheet_a_file_does_not_have(self):
        """A position a file does not have is left out for that file."""
        self.assertEqual(parts(_selection.of(GROUP, sheet="2")), [B])

    def test_the_order_written(self):
        """In each file, sheets come back in the order written."""
        self.assertEqual(parts(_selection.of(GROUP, sheet="2;1")), [B, A, C])


class TestRecords(unittest.TestCase):
    """of: which records a call names."""

    def test_the_header_is_kept(self):
        """A sheet cut to one record is still a sheet."""
        self.assertEqual(
            parts(_selection.of([SECOND], records="2")),
            [{"sheet name": "C", "header": ["k"], "records": [["y"]]}],
        )

    def test_a_record_that_does_not_exist(self):
        """A record that does not exist is left out, not refused."""
        part = parts(_selection.of([SECOND], records="4"))[0]
        self.assertEqual(part["records"], [])

    def test_the_condition_comes_first(self):
        """records counts the records the condition keeps."""
        selection = _selection.of([SECOND], records="1", condition=keep_y)
        self.assertEqual(parts(selection)[0]["records"], [["y"]])

    def test_counts(self):
        """CSVW, 4.4: the records of the sheet, and those it keeps."""
        entry = _selection.of([SECOND], condition=keep_y)[0]
        self.assertEqual((entry["records"], entry["matches"]), (3, 1))

    def test_matches_without_a_condition(self):
        """With no condition, every record matches."""
        entry = _selection.of([SECOND])[0]
        self.assertEqual((entry["records"], entry["matches"]), (3, 3))

    def test_positions(self):
        """CSVW, 4.4: each record named keeps its place in the sheet."""
        with self.subTest("all"):
            self.assertEqual(_selection.of([SECOND])[0]["positions"], [1, 2, 3])
        with self.subTest("named"):
            entry = _selection.of([SECOND], records="3;1")[0]
            self.assertEqual(entry["positions"], [3, 1])
        with self.subTest("kept by the condition"):
            entry = _selection.of([SECOND], records="1", condition=keep_y)[0]
            self.assertEqual(entry["positions"], [2])

    def test_positions_are_of_records_not_fields(self):
        """A record that does not exist names none; fields cut none."""
        with self.subTest("a record that does not exist"):
            self.assertEqual(_selection.of([SECOND], records="4")[0]["positions"], [])
        with self.subTest("no field named"):
            entry = _selection.of([SECOND], fields="2")[0]
            self.assertEqual(entry["positions"], [1, 2, 3])


class TestFields(unittest.TestCase):
    """of: which fields a call names."""

    def test_the_header_is_cut_alike(self):
        """Header and records are cut by the same positions."""
        self.assertEqual(
            parts(_selection.of([FIRST], sheet="1", fields="1;3")),
            [{"sheet name": "A", "header": ["a", "c"], "records": [["1", "3"]]}],
        )

    def test_an_empty_sheet(self):
        """A sheet with no lines has no field, and stays empty."""
        self.assertEqual(parts(_selection.of([FIRST], sheet="2", fields="1")), [B])

    def test_no_field_named(self):
        """The draft, Data Model: a sheet left no field is empty."""
        self.assertEqual(
            parts(_selection.of([SECOND], fields="2")),
            [{"sheet name": "C", "header": None, "records": []}],
        )

    def test_sheets_of_two_widths(self):
        """Each sheet keeps the fields it has; the counts stay."""
        selection = _selection.of(GROUP, sheet="1", fields="2-3")
        self.assertEqual(
            parts(selection),
            [
                {"sheet name": "A", "header": ["b", "c"], "records": [["2", "3"]]},
                {"sheet name": "C", "header": None, "records": []},
            ],
        )
        self.assertEqual(selection[1]["records"], 3)

    def test_the_condition_sees_the_whole_record(self):
        """fields cuts after the condition has seen every field."""
        selection = _selection.of(
            [FIRST], sheet="1", fields="1", condition=keep_third_is_3
        )
        self.assertEqual(parts(selection)[0]["records"], [["1"]])


class TestRefused(unittest.TestCase):
    """of: a selection not written as the syntax writes one."""

    def test_refused_with_nothing_to_choose_from(self):
        """A selection is checked whatever the group holds."""
        for name in ("sheet", "records", "fields"):
            with self.subTest(name):
                with self.assertRaises(_refusal.ValueRefusalError):
                    _selection.of([], **{name: "x"})
