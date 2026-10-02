"""Test text_spreadsheet._map against the draft.

Classes:
TestOf -- of: the names of the fields of each sheet
"""

__all__ = ["TestOf"]

import unittest

import mtsv

from text_spreadsheet import _map, _selection

SHEETS = [
    {"sheet name": "People", "header": ["Name", "Age"], "records": [["Ada", "36"]]},
    {"sheet name": "Empty", "header": None, "records": []},
]
NOTES = [{"sheet name": "Notes", "header": ["Key"], "records": [["a"], ["b"]]}]
GROUP = [{"file": 1, "sheets": SHEETS}, {"file": 2, "sheets": NOTES}]


class TestOf(unittest.TestCase):
    """of: the names of the fields of each sheet."""

    def setUp(self):
        """Map the whole group."""
        self.value = _map.of(_selection.of(GROUP))

    def test_one_sheet(self):
        """The map answers with one sheet, fields."""
        self.assertEqual([sheet["sheet name"] for sheet in self.value], ["fields"])

    def test_fields(self):
        """Each field of a header: its file, sheet, position, name."""
        fields = self.value[0]
        self.assertEqual(fields["header"], ["file", "sheet", "field", "field name"])
        self.assertEqual(
            fields["records"],
            [
                ["1", "1", "1", "Name"],
                ["1", "1", "2", "Age"],
                ["2", "1", "1", "Key"],
            ],
        )

    def test_fields_follow_the_selection(self):
        """A sheet chosen alone keeps its file and its position."""
        value = _map.of(_selection.of(GROUP[1:2]))
        self.assertEqual(value[0]["records"], [["2", "1", "1", "Key"]])

    def test_the_map_is_mtsv(self):
        """The map is itself a file the generator can write."""
        self.assertEqual(mtsv.loads(mtsv.dumps(self.value)), self.value)
