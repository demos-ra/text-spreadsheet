"""Test text_spreadsheet._slice against RFC 7111 and the Data Model."""

import unittest

from text_spreadsheet import _slice

SHEETS = [
    {"sheet name": "A", "header": ["a", "b", "c"], "records": [["1", "2", "3"]]},
    {"sheet name": "B", "header": None, "records": []},
    {
        "sheet name": "C",
        "header": ["k"],
        "records": [["x"], ["y"], ["z"]],
    },
]


class TestSheets(unittest.TestCase):
    """of: which sheets an address names."""

    def test_all_of_them(self):
        """No address names every sheet."""
        self.assertEqual(_slice.of(SHEETS), SHEETS)

    def test_one(self):
        """A position names one sheet."""
        self.assertEqual(_slice.of(SHEETS, sheet="2"), [SHEETS[1]])

    def test_a_list(self):
        """RFC 7111, 3: specs joined by ";"."""
        self.assertEqual(_slice.of(SHEETS, sheet="1;3"), [SHEETS[0], SHEETS[2]])

    def test_a_range(self):
        """RFC 7111, 3: two positions joined by "-"."""
        self.assertEqual(_slice.of(SHEETS, sheet="1-3"), SHEETS)

    def test_the_order_written(self):
        """Sheets come back in the order the address writes them."""
        self.assertEqual(_slice.of(SHEETS, sheet="3;1"), [SHEETS[2], SHEETS[0]])


class TestRecords(unittest.TestCase):
    """of: which records an address names."""

    def test_a_range(self):
        """The records named come back under their header."""
        self.assertEqual(
            _slice.of(SHEETS, sheet="3", rows="1-2"),
            [{"sheet name": "C", "header": ["k"], "records": [["x"], ["y"]]}],
        )

    def test_the_header_is_kept(self):
        """A sheet cut to one record is still a sheet."""
        value = _slice.of(SHEETS, sheet="3", rows="2")
        self.assertEqual(value[0]["header"], ["k"])

    def test_past_the_end(self):
        """A record the sheet does not have is refused."""
        with self.assertRaises(ValueError):
            _slice.of(SHEETS, sheet="3", rows="4")


class TestFields(unittest.TestCase):
    """of: which fields an address names."""

    def test_the_header_is_cut_alike(self):
        """Header and records are cut by the same positions."""
        self.assertEqual(
            _slice.of(SHEETS, sheet="1", fields="1;3"),
            [{"sheet name": "A", "header": ["a", "c"], "records": [["1", "3"]]}],
        )

    def test_all_three_axes(self):
        """Sheet, records and fields compose."""
        self.assertEqual(
            _slice.of(SHEETS, sheet="1", rows="1", fields="2"),
            [{"sheet name": "A", "header": ["b"], "records": [["2"]]}],
        )

    def test_an_empty_sheet(self):
        """A sheet with no lines has no field to name, so it is refused."""
        with self.assertRaises(ValueError):
            _slice.of(SHEETS, sheet="2", fields="1")

    def test_past_the_end(self):
        """A field the sheet does not have is refused."""
        with self.assertRaises(ValueError):
            _slice.of(SHEETS, sheet="1", fields="4")


class TestAddress(unittest.TestCase):
    """of: what is not an address."""

    def test_refused(self):
        """Anything but positions and ranges of them is refused."""
        for address in ("a", "", "1-", "-1", "1,2", "1-2-3", "1 2"):
            with self.subTest(address):
                with self.assertRaises(ValueError):
                    _slice.of(SHEETS, sheet=address)

    def test_counts_from_one(self):
        """Position 0 is refused: positions count from 1."""
        with self.assertRaises(ValueError):
            _slice.of(SHEETS, sheet="0")

    def test_backwards_range(self):
        """A range that ends before it starts is refused."""
        with self.assertRaises(ValueError):
            _slice.of(SHEETS, sheet="3-1")
