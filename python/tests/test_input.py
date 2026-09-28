"""Test text_spreadsheet._input against POSIX and CSVW."""

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import mtsv

from text_spreadsheet import _cache, _input, _refusal

import support

SHEETS = [{"sheet name": "People", "header": ["Name"], "records": [["Ada"]]}]


class Folder(unittest.TestCase):
    """A temporary folder, and the copies a test leaves in the cache."""

    def setUp(self):
        """Make the folder."""
        self.directory = tempfile.TemporaryDirectory()
        self.folder = Path(self.directory.name)

    def tearDown(self):
        """Remove the folder and the copies made from it."""
        cache = _cache.artifact(self.folder / "x").parent
        shutil.rmtree(cache, ignore_errors=True)
        self.directory.cleanup()

    def write(self, name, value=SHEETS):
        """Write sheets, or bytes, to a file in the folder."""
        path = self.folder / name
        with path.open("wb") as fp:
            if isinstance(value, bytes):
                fp.write(value)
            else:
                mtsv.dump(value, fp)
        return path


class TestPath(Folder):
    """of: what a path names."""

    def test_relative_refused(self):
        """A path that is not absolute is refused, as ValueError."""
        with self.assertRaises(_refusal.ValueRefusalError):
            _input.of("book.mtsv")

    def test_a_file(self):
        """A file names a group of one."""
        group = _input.of(str(self.write("book.mtsv")))
        self.assertEqual(
            [(file["file"], file["status"]) for file in group], [(1, "read")]
        )

    def test_no_format_refused(self):
        """A file named directly, of no format, is refused."""
        with self.assertRaises(_refusal.LookupRefusalError):
            _input.of(str(self.write("book.txt", b"a\n")))

    def test_unreadable_refused(self):
        """A file named directly that does not exist is refused."""
        with self.assertRaises(_refusal.OSRefusalError):
            _input.of(str(self.folder / "absent.xlsx"))


class TestFolder(Folder):
    """of: the members of a folder."""

    def test_members_in_byte_order(self):
        """POSIX 2.13.3: names sorted byte by byte."""
        for name in ("b.mtsv", "B.mtsv", "a.mtsv", "é.mtsv"):
            self.write(name)
        names = [file["source"].name for file in _input.of(str(self.folder))]
        self.assertEqual(names, ["B.mtsv", "a.mtsv", "b.mtsv", "é.mtsv"])

    def test_hidden_and_subfolders_left_out(self):
        """A name beginning with "." and a subfolder are not members."""
        self.write("a.mtsv")
        self.write(".hidden.mtsv")
        (self.folder / "sub").mkdir()
        names = [file["source"].name for file in _input.of(str(self.folder))]
        self.assertEqual(names, ["a.mtsv"])

    def test_a_link_is_followed(self):
        """A symbolic link names the file it points to."""
        target = self.write("a.mtsv")
        (self.folder / "b.mtsv").symlink_to(target)
        group = _input.of(str(self.folder))
        self.assertEqual([file["sheets"] for file in group], [SHEETS, SHEETS])

    def test_statuses(self):
        """Each member is read, of no format, or failed."""
        self.write("a.mtsv")
        self.write("b.txt", b"x\n")
        self.write("c.mtsv", b"a\tb\nc\n")
        group = _input.of(str(self.folder))
        self.assertEqual(
            [file["status"].split(":")[0] for file in group],
            ["read", "no format", "failed"],
        )

    def test_a_fault_is_not_a_failure(self):
        """An error that is not a refusal is not named as one."""
        self.write("a.mtsv")
        with mock.patch("text_spreadsheet._conversion.of", side_effect=KeyError("k")):
            with self.assertRaises(KeyError):
                _input.of(str(self.folder))

    def test_nothing_where_nothing_converted(self):
        """A member not read has no artifact, text or sheets."""
        self.write("b.txt", b"x\n")
        file = _input.of(str(self.folder))[0]
        self.assertEqual(
            (file["artifact"], file["converted"], file["text"], file["sheets"]),
            (None, False, "", []),
        )

    def test_an_unwritable_name(self):
        """A name holding a tab cannot be written: failed."""
        self.write("a\tb.mtsv")
        file = _input.of(str(self.folder))[0]
        self.assertEqual(file["status"], "failed: name cannot be written")

    def test_empty(self):
        """A folder with no members is a group of none."""
        self.assertEqual(_input.of(str(self.folder)), [])

    def test_numbered(self):
        """Members count from 1, in order."""
        self.write("a.mtsv")
        self.write("b.mtsv")
        group = _input.of(str(self.folder))
        self.assertEqual([file["file"] for file in group], [1, 2])
