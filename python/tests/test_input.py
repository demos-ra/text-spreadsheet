"""Test text_spreadsheet._input against POSIX and CSVW.

Classes:
TestPathname -- of: what a pathname names
TestDirectory -- of: the members of a directory
"""

__all__ = ["TestPathname", "TestDirectory"]

import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import mtsv

from text_spreadsheet import _cache, _input, _refusal

import support

SHEETS = [{"sheet name": "People", "header": ["Name"], "records": [["Ada"]]}]


class Directory(unittest.TestCase):
    """A temporary directory, and the copies its tests leave."""

    def setUp(self):
        """Make the directory."""
        self.temporary = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary.name)

    def tearDown(self):
        """Remove the directory and the copies made from it."""
        copies = _cache.location(self.directory / "x").parent
        shutil.rmtree(copies, ignore_errors=True)
        self.temporary.cleanup()

    def write(self, name, value=SHEETS):
        """Write sheets, or bytes, to a file in the directory."""
        pathname = self.directory / name
        with pathname.open("wb") as fp:
            if isinstance(value, bytes):
                fp.write(value)
            else:
                mtsv.dump(value, fp)
        return pathname


class TestPathname(Directory):
    """of: what a pathname names."""

    def test_relative_refused(self):
        """A pathname that is not absolute is refused, as ValueError."""
        with self.assertRaises(_refusal.ValueRefusalError):
            _input.of("book.mtsv")

    def test_a_file(self):
        """A file names a group of one."""
        group = _input.of(str(self.write("book.mtsv")))
        self.assertEqual(
            [(file["file"], file["not read"]) for file in group], [(1, None)]
        )

    def test_no_format_refused(self):
        """A file named directly, of no format, is refused."""
        with self.assertRaises(_refusal.LookupRefusalError):
            _input.of(str(self.write("book.txt", b"a\n")))

    def test_unreadable_refused(self):
        """A file named directly that does not exist is refused."""
        with self.assertRaises(_refusal.OSRefusalError):
            _input.of(str(self.directory / "absent.xlsx"))

    def test_not_a_regular_file_refused(self):
        """Neither a regular file nor a directory: refused."""
        os.mkfifo(self.directory / "pipe.mtsv")
        with self.assertRaises(_refusal.OSRefusalError):
            _input.of(str(self.directory / "pipe.mtsv"))

    def test_an_unwritable_name_refused(self):
        """A file named directly whose name holds a tab is refused."""
        pathname = self.write("a\tb.mtsv")
        with self.assertRaises(_refusal.ValueRefusalError) as caught:
            _input.of(str(pathname))
        self.assertEqual(str(caught.exception), "name cannot be written")


class TestDirectory(Directory):
    """of: the members of a directory."""

    def test_members_in_byte_order(self):
        """POSIX 2.13.3: names sorted byte by byte."""
        for name in ("b.mtsv", "B.mtsv", "a.mtsv", "é.mtsv"):
            self.write(name)
        names = [file["source"].name for file in _input.of(str(self.directory))]
        self.assertEqual(names, ["B.mtsv", "a.mtsv", "b.mtsv", "é.mtsv"])

    def test_hidden_left_out(self):
        """POSIX 2.13.3: a name beginning with "." is not a member."""
        self.write("a.mtsv")
        self.write(".hidden.mtsv")
        names = [file["source"].name for file in _input.of(str(self.directory))]
        self.assertEqual(names, ["a.mtsv"])

    def test_a_directory_is_skipped(self):
        """A directory within it is named, skipped, and not read."""
        self.write("a.mtsv")
        (self.directory / "sub").mkdir()
        self.write("sub/b.mtsv")
        group = _input.of(str(self.directory))
        self.assertEqual(
            [(file["source"].name, file["not read"]) for file in group],
            [("a.mtsv", None), ("sub", "skipped: directory")],
        )
        self.assertEqual(group[1]["sheets"], [])

    def test_not_a_regular_file_is_skipped(self):
        """A FIFO is named, skipped, and not read."""
        os.mkfifo(self.directory / "pipe.mtsv")
        file = _input.of(str(self.directory))[0]
        self.assertEqual(file["not read"], "skipped: not a regular file")

    def test_a_link_is_followed(self):
        """A symbolic link names the file it points to."""
        target = self.write("a.mtsv")
        (self.directory / "b.mtsv").symlink_to(target)
        group = _input.of(str(self.directory))
        self.assertEqual([file["sheets"] for file in group], [SHEETS, SHEETS])

    def test_statuses(self):
        """Each member is read, of no format, or failed."""
        self.write("a.mtsv")
        self.write("b.txt", b"x\n")
        self.write("c.mtsv", b"a\tb\nc\n")
        group = _input.of(str(self.directory))
        self.assertIsNone(group[0]["not read"])
        self.assertEqual(
            [file["not read"].split(":")[0] for file in group[1:]],
            ["no format", "failed"],
        )

    def test_a_fault_is_not_a_failure(self):
        """An error that is not a refusal is not named as one."""
        self.write("a.mtsv")
        with mock.patch("text_spreadsheet._conversion.of", side_effect=KeyError("k")):
            with self.assertRaises(KeyError):
                _input.of(str(self.directory))

    def test_nothing_where_nothing_converted(self):
        """A member not read has nothing left behind, and no sheets."""
        self.write("b.txt", b"x\n")
        file = _input.of(str(self.directory))[0]
        self.assertEqual((file["left behind"], file["sheets"]), ([], []))

    def test_an_unwritable_name(self):
        """A name holding a tab cannot be written: failed."""
        self.write("a\tb.mtsv")
        file = _input.of(str(self.directory))[0]
        self.assertEqual(file["not read"], "failed: name cannot be written")

    def test_empty(self):
        """A directory with no members is a group of none."""
        self.assertEqual(_input.of(str(self.directory)), [])

    def test_numbered(self):
        """Members count from 1, in order."""
        self.write("a.mtsv")
        self.write("b.mtsv")
        group = _input.of(str(self.directory))
        self.assertEqual([file["file"] for file in group], [1, 2])
