"""Test text_spreadsheet._filter against RFC 9535 and RFC 9485."""

import unittest

from text_spreadsheet import _filter, _refusal

RECORDS = [
    ["Paul", "23", "1115 W Franklin"],
    ["Zeke", "45", "W Main St"],
    ["Émile", "7", "Rue Haute"],
]


def kept(filter):
    """Return the positions a filter keeps of RECORDS."""
    return _filter.matches(_filter.compile(filter), RECORDS)


class TestFilter(unittest.TestCase):
    """compile and matches: which records a filter keeps."""

    def test_equality(self):
        """RFC 9535, 2.3.5.2.2: == on text, @[i] from 0."""
        self.assertEqual(kept("@[0] == 'Zeke'"), [2])

    def test_exact(self):
        """RFC 9535, 2.3.1.2: text is compared exactly."""
        self.assertEqual(kept("@[0] == 'zeke'"), [])

    def test_text_order(self):
        """RFC 9535, 2.3.5.2.2: text is ordered by scalar value."""
        self.assertEqual(kept("@[1] > '3'"), [2, 3])

    def test_a_number_is_not_text(self):
        """RFC 9535, 2.3.5.2.2: a number never equals a string."""
        self.assertEqual(kept("@[1] == 45"), [])

    def test_logic(self):
        """RFC 9535, 2.3.5.1: &&, || and !."""
        self.assertEqual(kept("@[0] == 'Paul' || !(@[1] == '7')"), [1, 2])

    def test_match_and_search(self):
        """RFC 9535, 2.4.6 and 2.4.7: the whole value, or any part."""
        with self.subTest("match"):
            self.assertEqual(kept("match(@[1], '[0-9]+')"), [1, 2, 3])
        with self.subTest("search"):
            self.assertEqual(kept("search(@[2], 'Main')"), [2])

    def test_unicode_categories(self):
        """RFC 9485, 3: \\p{Lu} matches any uppercase letter."""
        self.assertEqual(kept("match(@[0], '\\\\p{Lu}.*')"), [1, 2, 3])

    def test_outside_i_regexp(self):
        """RFC 9535, 2.4.6: a pattern not I-Regexp matches nothing."""
        self.assertEqual(kept("match(@[1], '\\\\d+')"), [])

    def test_the_other_functions(self):
        """RFC 9535, 2.4.4, 2.4.5 and 2.4.8: length, count and value."""
        with self.subTest("length"):
            self.assertEqual(kept("length(@[0]) == 4"), [1, 2])
        with self.subTest("count"):
            self.assertEqual(kept("count(@[*]) == 3"), [1, 2, 3])
        with self.subTest("value"):
            self.assertEqual(kept("value(@[0]) == 'Paul'"), [1])

    def test_a_missing_field(self):
        """RFC 9535, 2.3.3.2: a missing field selects nothing."""
        self.assertEqual(kept("@[9] == 'x'"), [])

    def test_root_is_the_records(self):
        """RFC 9535, 2.2.2: $ is the records the filter selects from."""
        self.assertEqual(kept("@[0] == $[0][0]"), [1])


class TestRefused(unittest.TestCase):
    """compile: what is not a filter."""

    def test_not_well_formed(self):
        """RFC 9535, 2.1: a query that is not well-formed is refused."""
        for filter in ("@[0] = 'x'", "", "@[0] ==", "("):
            with self.subTest(filter):
                with self.assertRaises(_refusal.ValueRefusalError):
                    _filter.compile(filter)

    def test_one_filter_selector(self):
        """RFC 9535, 4.2: a filter cannot add a selector."""
        for filter in ("@[0] == 'x', 0", "@[0] == 'x'].a[?true"):
            with self.subTest(filter):
                with self.assertRaises(_refusal.ValueRefusalError):
                    _filter.compile(filter)
