"""Test text_spreadsheet._positions against RFC 7111."""

import unittest

from text_spreadsheet import _positions, _refusal


class TestSyntax(unittest.TestCase):
    """of: how an address is written."""

    def test_one(self):
        """A position names one."""
        self.assertEqual(_positions.of("2", 5), [2])

    def test_a_list(self):
        """RFC 7111, 3: specs joined by ";", in the order written."""
        self.assertEqual(_positions.of("3;1", 5), [3, 1])

    def test_a_range(self):
        """RFC 7111, 3: two positions joined by "-"."""
        self.assertEqual(_positions.of("2-4", 5), [2, 3, 4])

    def test_the_last(self):
        """RFC 7111, 3: "*" is the last position."""
        with self.subTest("alone"):
            self.assertEqual(_positions.of("*", 5), [5])
        with self.subTest("ending a range"):
            self.assertEqual(_positions.of("4-*", 5), [4, 5])

    def test_refused(self):
        """Anything not written as the syntax writes it is refused."""
        for address in ("a", "", "1-", "-1", "1,2", "1-2-3", "1 2", "**"):
            with self.subTest(address):
                with self.assertRaises(_refusal.ValueRefusalError):
                    _positions.of(address, 5)


class TestSemantics(unittest.TestCase):
    """of: what an address names, RFC 7111, 4.2."""

    def test_a_position_that_does_not_exist(self):
        """A single selection of a non-existing row is ignored."""
        self.assertEqual(_positions.of("6", 5), [])

    def test_zero_does_not_exist(self):
        """Rows are counted from one, so 0 names nothing."""
        self.assertEqual(_positions.of("0", 5), [])

    def test_a_range_extends_only_to_the_actual_size(self):
        """A range past the size stops at the size."""
        self.assertEqual(_positions.of("4-9", 5), [4, 5])

    def test_a_range_from_zero(self):
        """A range from 0 extends only to the actual size, from 1."""
        self.assertEqual(_positions.of("0-2", 5), [1, 2])

    def test_an_inverse_range_is_ignored(self):
        """A range that ends before it starts names nothing."""
        self.assertEqual(_positions.of("4-2", 5), [])

    def test_each_spec_stands_alone(self):
        """What is ignored does not fail the rest."""
        self.assertEqual(_positions.of("1-2;5-4;13-16", 5), [1, 2])

    def test_overlaps_are_kept(self):
        """Each spec returns what it names, a position even twice."""
        self.assertEqual(_positions.of("1-3;2", 5), [1, 2, 3, 2])

    def test_nothing_to_choose(self):
        """With none to choose from, every address names nothing."""
        for address in ("1", "*", "1-*"):
            with self.subTest(address):
                self.assertEqual(_positions.of(address, 0), [])
