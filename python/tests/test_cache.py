"""Test text_spreadsheet._cache: platformdirs, RFC 9111, POSIX.

Classes:
TestLocation -- location: where the MTSV copy of a file is kept
TestStoreAndLoad -- store and load: a copy, and what was left behind
TestIsFresh -- is_fresh: whether a stored copy may be used
"""

__all__ = ["TestLocation", "TestStoreAndLoad", "TestIsFresh"]

import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from text_spreadsheet import _cache

import support

TEXT = "\fPeople\nName\nAda\n"


class TestLocation(unittest.TestCase):
    """location: where the MTSV copy of a source file is kept."""

    def setUp(self):
        """Make a directory, and take its resolved pathname."""
        self.directory = tempfile.TemporaryDirectory()
        self.resolved = Path(os.path.realpath(self.directory.name))

    def tearDown(self):
        """Remove the directory."""
        self.directory.cleanup()

    def mirrored(self, name):
        """Return where the copy of a name in the directory is kept."""
        return support.CACHE.joinpath(*self.resolved.parts[1:], name + ".mtsv")

    def test_asks_platformdirs(self):
        """platformdirs: user_cache_dir, with the appname."""
        _cache.location(self.resolved / "book.xlsx")
        support.user_cache_dir.assert_called_with("text-spreadsheet")

    def test_mirrors_the_resolved_pathname(self):
        """The resolved pathname is mirrored, with MTSV added."""
        self.assertEqual(
            _cache.location(self.resolved / "book.xlsx"), self.mirrored("book.xlsx")
        )

    def test_dot_dot_reaches_the_same_copy(self):
        """POSIX realpath: the resolution does not involve '..'."""
        (self.resolved / "sub").mkdir()
        dotted = self.resolved / "sub" / ".." / "book.xlsx"
        self.assertEqual(_cache.location(dotted), self.mirrored("book.xlsx"))

    def test_dot_dot_at_the_root_stays_under_the_cache(self):
        """A copy never leaves the cache directory."""
        dotted = Path("/..", *self.resolved.parts[1:], "book.xlsx")
        self.assertEqual(_cache.location(dotted), self.mirrored("book.xlsx"))

    def test_a_link_reaches_the_same_copy(self):
        """POSIX realpath: the resolution involves no symbolic link."""
        (self.resolved / "book.xlsx").write_bytes(b"")
        (self.resolved / "link.xlsx").symlink_to(self.resolved / "book.xlsx")
        self.assertEqual(
            _cache.location(self.resolved / "link.xlsx"), self.mirrored("book.xlsx")
        )

    def test_two_directories_do_not_collide(self):
        """One name in two directories gives two copies."""
        self.assertNotEqual(
            _cache.location(self.resolved / "me" / "book.xlsx"),
            _cache.location(self.resolved / "you" / "book.xlsx"),
        )

    def test_the_whole_name_is_kept(self):
        """Whatever the format, the copy is MTSV; two never collide."""
        names = ("book.xlsx", "book.ods", "book.sqlite", "book.parquet")
        copies = [_cache.location(self.resolved / name) for name in names]
        self.assertEqual(len(set(copies)), len(names))
        for name, copy in zip(names, copies):
            with self.subTest(name):
                self.assertEqual(copy.name, name + ".mtsv")


class TestStoreAndLoad(unittest.TestCase):
    """store and load: a copy, and what its conversion left behind."""

    def test_round_trip(self):
        """What is stored is loaded."""
        with tempfile.TemporaryDirectory() as directory:
            stored = Path(directory, "book.xlsx.mtsv")
            _cache.store(stored, TEXT, ["cell type n"])
            self.assertEqual(_cache.load(stored), (TEXT, ["cell type n"]))

    def test_metadata_beside_the_copy(self):
        """CSVW 5.3: the copy's name with -metadata.mtsv added."""
        with tempfile.TemporaryDirectory() as directory:
            stored = Path(directory, "book.xlsx.mtsv")
            _cache.store(stored, TEXT, [])
            self.assertEqual(
                sorted(one.name for one in Path(directory).iterdir()),
                ["book.xlsx.mtsv", "book.xlsx.mtsv-metadata.mtsv"],
            )

    def test_damaged_metadata(self):
        """Metadata not as store writes it raises ValueError."""
        with tempfile.TemporaryDirectory() as directory:
            stored = Path(directory, "book.xlsx.mtsv")
            _cache.store(stored, TEXT, [])
            Path(directory, "book.xlsx.mtsv-metadata.mtsv").write_bytes(b"x\n")
            with self.assertRaises(ValueError):
                _cache.load(stored)

    def test_makes_the_directories(self):
        """XDG: directories that do not exist are made, as 0700."""
        with tempfile.TemporaryDirectory() as directory:
            stored = Path(directory, "home", "me", "book.xlsx.mtsv")
            _cache.store(stored, TEXT, [])
            self.assertTrue(stored.exists())
            for made in (stored.parent, stored.parent.parent):
                with self.subTest(made.name):
                    self.assertEqual(made.stat().st_mode & 0o777, 0o700)

    def test_leaves_a_directory_that_exists(self):
        """XDG: the permissions of an existing directory are kept."""
        with tempfile.TemporaryDirectory() as directory:
            existing = Path(directory, "home")
            existing.mkdir(mode=0o755)
            before = existing.stat().st_mode
            _cache.store(existing / "book.xlsx.mtsv", TEXT, [])
            self.assertEqual(existing.stat().st_mode, before)

    def test_replaces_an_older_copy(self):
        """A second copy takes the place of the first."""
        with tempfile.TemporaryDirectory() as directory:
            stored = Path(directory, "book.xlsx.mtsv")
            _cache.store(stored, TEXT, ["a"])
            _cache.store(stored, "", ["b"])
            self.assertEqual(_cache.load(stored), ("", ["b"]))

    def test_nothing_left_after_an_error(self):
        """POSIX 1.4: a working file is removed when the write fails."""
        with tempfile.TemporaryDirectory() as directory:
            stored = Path(directory, "book.xlsx.mtsv")
            stored.mkdir()
            with self.assertRaises(OSError):
                _cache.store(stored, TEXT, [])
            self.assertEqual(
                sorted(one.name for one in Path(directory).iterdir()),
                ["book.xlsx.mtsv", "book.xlsx.mtsv-metadata.mtsv"],
            )

    def test_working_name_is_the_process_and_thread(self):
        """POSIX 1.4: two writers write under two working names."""
        with tempfile.TemporaryDirectory() as directory:
            stored = Path(directory, "book.xlsx.mtsv")
            written = []
            original = Path.write_bytes

            def spy(pathname, data):
                written.append(pathname.name)
                return original(pathname, data)

            with mock.patch.object(Path, "write_bytes", spy):
                with mock.patch("os.getpid", return_value=7):
                    with mock.patch("threading.get_ident", return_value=3):
                        _cache.store(stored, TEXT, [])
            self.assertEqual(
                written,
                [
                    "book.xlsx.mtsv-metadata.mtsv.7.3.part",
                    "book.xlsx.mtsv.7.3.part",
                ],
            )

    def test_threads_store_one_copy(self):
        """Calls in threads of one process each keep the copy whole."""
        with tempfile.TemporaryDirectory() as directory:
            stored = Path(directory, "book.xlsx.mtsv")
            text = TEXT + "Ada\n" * 100000
            errors = []

            def store():
                try:
                    _cache.store(stored, text, [])
                except OSError as error:
                    errors.append(error)

            threads = [threading.Thread(target=store) for _ in range(8)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            self.assertEqual(errors, [])
            self.assertEqual(_cache.load(stored), (text, []))


class TestIsFresh(unittest.TestCase):
    """is_fresh: whether a stored copy may be used."""

    def test_no_copy(self):
        """A copy that does not exist is not fresh."""
        with tempfile.TemporaryDirectory() as directory:
            stored = Path(directory, "book.xlsx.mtsv")
            self.assertFalse(_cache.is_fresh(stored, 0))

    def test_copy_newer(self):
        """A copy newer than its source, with metadata, is fresh."""
        with tempfile.TemporaryDirectory() as directory:
            stored = Path(directory, "book.xlsx.mtsv")
            _cache.store(stored, TEXT, [])
            self.assertTrue(_cache.is_fresh(stored, 0))

    def test_copy_without_metadata(self):
        """A copy without its metadata is not fresh."""
        with tempfile.TemporaryDirectory() as directory:
            stored = Path(directory, "book.xlsx.mtsv")
            stored.write_bytes(b"")
            self.assertFalse(_cache.is_fresh(stored, 0))

    def test_a_copy_that_cannot_be_examined(self):
        """XDG, Basics: a copy that cannot be examined is not fresh."""
        with tempfile.TemporaryDirectory() as directory:
            stored = Path(directory, "book.xlsx.mtsv")
            _cache.store(stored, TEXT, [])
            with mock.patch.object(Path, "stat", side_effect=PermissionError):
                self.assertFalse(_cache.is_fresh(stored, 0))

    def test_source_newer(self):
        """A source changed after its copy is stale."""
        with tempfile.TemporaryDirectory() as directory:
            stored = Path(directory, "book.xlsx.mtsv")
            _cache.store(stored, TEXT, [])
            os.utime(stored, (0, 0))
            self.assertFalse(_cache.is_fresh(stored, 1))
