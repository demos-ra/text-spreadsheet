"""Test text_spreadsheet._positions against RFC 7111.

Classes:
TestSyntax -- specs: how a selection is written
TestSemantics -- of: what a selection names
TestSelection -- selection: the selection that names positions
"""

__all__ = ["TestSyntax", "TestSemantics", "TestSelection"]

import unittest

from text_spreadsheet import _positions, _refusal


def named(selection, count):
    """Return the positions a selection names, of so many."""
    return _positions.of(_positions.specs(selection), count)


class TestSyntax(unittest.TestCase):
    """specs: how a selection is written."""

    def test_one(self):
        """A position is a spec of one: its first and its last."""
        self.assertEqual(_positions.specs("2"), [("2", "2")])

    def test_a_list(self):
        """RFC 7111, 3: specs joined by ";", in the order written."""
        self.assertEqual(_positions.specs("3;1"), [("3", "3"), ("1", "1")])

    def test_a_range(self):
        """RFC 7111, 3: two positions joined by "-"."""
        self.assertEqual(_positions.specs("2-4"), [("2", "4")])

    def test_the_last(self):
        """RFC 7111, 3: "*" is a position."""
        self.assertEqual(_positions.specs("4-*;*"), [("4", "*"), ("*", "*")])

    def test_refused(self):
        """Anything not written as the syntax writes it is refused."""
        for selection in ("a", "", "1-", "-1", "1,2", "1-2-3", "1 2", "**"):
            with self.subTest(selection):
                with self.assertRaises(_refusal.ValueRefusalError):
                    _positions.specs(selection)


class TestSemantics(unittest.TestCase):
    """of: what a selection names, RFC 7111, 4.2."""

    def test_in_the_order_written(self):
        """The positions come in the order the specs are written."""
        self.assertEqual(named("3;1", 5), [3, 1])

    def test_a_range(self):
        """A range names each position from its first to its last."""
        self.assertEqual(named("2-4", 5), [2, 3, 4])

    def test_the_last(self):
        """ "*" refers to the last row or column."""
        with self.subTest("alone"):
            self.assertEqual(named("*", 5), [5])
        with self.subTest("ending a range"):
            self.assertEqual(named("4-*", 5), [4, 5])

    def test_a_position_that_does_not_exist(self):
        """A single selection of a non-existing row is ignored."""
        self.assertEqual(named("6", 5), [])

    def test_zero_does_not_exist(self):
        """Rows are counted from one, so 0 names nothing."""
        self.assertEqual(named("0", 5), [])

    def test_a_range_extends_only_to_the_actual_size(self):
        """A range past the size stops at the size."""
        self.assertEqual(named("4-9", 5), [4, 5])

    def test_a_range_from_zero(self):
        """A range from 0 extends only to the actual size, from 1."""
        self.assertEqual(named("0-2", 5), [1, 2])

    def test_an_inverse_range_is_ignored(self):
        """A range that ends before it starts names nothing."""
        self.assertEqual(named("4-2", 5), [])

    def test_each_spec_stands_alone(self):
        """What is ignored does not fail the rest."""
        self.assertEqual(named("1-2;5-4;13-16", 5), [1, 2])

    def test_overlaps_are_kept(self):
        """Each spec returns what it names, a position even twice."""
        self.assertEqual(named("1-3;2", 5), [1, 2, 3, 2])

    def test_a_number_of_any_length(self):
        """RFC 7111, 3: number = 1*( DIGIT ), however many."""
        with self.subTest("alone"):
            self.assertEqual(named("9" * 5000, 5), [])
        with self.subTest("ending a range"):
            self.assertEqual(named("4-" + "9" * 5000, 5), [4, 5])
        with self.subTest("starting a range"):
            self.assertEqual(named("9" * 5000 + "-*", 5), [])
        with self.subTest("leading zeros"):
            self.assertEqual(named("0" * 5000 + "2", 5), [2])

    def test_nothing_to_choose(self):
        """With none to choose from, every selection names nothing."""
        for selection in ("1", "*", "1-*"):
            with self.subTest(selection):
                self.assertEqual(named(selection, 0), [])


class TestSelection(unittest.TestCase):
    """selection: the selection that names positions, RFC 7111, 3."""

    def test_one(self):
        """One position is written as itself."""
        self.assertEqual(_positions.selection([17]), "17")

    def test_a_run_is_a_range(self):
        """Consecutive positions are written as one range."""
        self.assertEqual(_positions.selection([40, 41, 42]), "40-42")

    def test_a_list(self):
        """Runs are joined by ";", in the order given."""
        self.assertEqual(_positions.selection([3, 17, 18, 5]), "3;17-18;5")

    def test_a_position_twice(self):
        """A position named twice is written twice."""
        self.assertEqual(_positions.selection([1, 2, 3, 2]), "1-3;2")

    def test_none(self):
        """No positions are written as the empty text."""
        self.assertEqual(_positions.selection([]), "")

    def test_names_the_same_positions(self):
        """What is written names the positions it was written from."""
        for positions in ([1], [2, 3, 4], [5, 1, 2, 2, 9]):
            with self.subTest(positions):
                written = _positions.selection(positions)
                self.assertEqual(named(written, 9), positions)
