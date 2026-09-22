"""Test text_spreadsheet._cache against platformdirs and RFC 9111."""

import os
import tempfile
import unittest
from pathlib import Path

from platformdirs import user_cache_dir

from text_spreadsheet import _cache

CACHE = Path(user_cache_dir("text-spreadsheet", appauthor=False))


class TestArtifact(unittest.TestCase):
    """artifact: where the MTSV copy of a source file is kept."""

    def test_under_the_cache_directory(self):
        """The copy sits under the user's cache directory."""
        path = _cache.artifact(Path("/home/me/book.xlsx"))
        self.assertEqual(path.parts[: len(CACHE.parts)], CACHE.parts)

    def test_mirrors_the_source_path(self):
        """The source path is mirrored, with MTSV added to the name."""
        self.assertEqual(
            _cache.artifact(Path("/home/me/book.xlsx")),
            CACHE / "home/me/book.xlsx.mtsv",
        )

    def test_two_folders_do_not_collide(self):
        """One name in two folders gives two copies."""
        self.assertNotEqual(
            _cache.artifact(Path("/home/me/book.xlsx")),
            _cache.artifact(Path("/home/you/book.xlsx")),
        )

    def test_the_whole_name_is_kept(self):
        """Whatever the format, the copy is MTSV, and two never collide."""
        names = ("book.xlsx", "book.ods", "book.sqlite", "book.parquet")
        paths = [_cache.artifact(Path("/home/me", name)) for name in names]
        self.assertEqual(len(set(paths)), len(names))
        for name, path in zip(names, paths):
            with self.subTest(name):
                self.assertEqual(path.name, name + ".mtsv")

    def test_relative_path_refused(self):
        """A path that is not absolute raises ValueError."""
        with self.assertRaises(ValueError):
            _cache.artifact(Path("book.xlsx"))


class TestIsFresh(unittest.TestCase):
    """is_fresh: whether a stored copy may be used."""

    def test_no_copy(self):
        """A copy that does not exist is not fresh."""
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory, "book.xlsx")
            source.write_bytes(b"")
            stored = Path(directory, "book.xlsx.mtsv")
            self.assertFalse(_cache.is_fresh(source, stored))

    def test_copy_newer(self):
        """A copy written after its source is fresh."""
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory, "book.xlsx")
            source.write_bytes(b"")
            stored = Path(directory, "book.xlsx.mtsv")
            stored.write_bytes(b"")
            os.utime(source, (0, 0))
            self.assertTrue(_cache.is_fresh(source, stored))

    def test_source_newer(self):
        """A source changed after its copy is stale."""
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory, "book.xlsx")
            source.write_bytes(b"")
            stored = Path(directory, "book.xlsx.mtsv")
            stored.write_bytes(b"")
            os.utime(stored, (0, 0))
            self.assertFalse(_cache.is_fresh(source, stored))


class TestStore(unittest.TestCase):
    """store: putting a copy where the copy lives."""

    def test_writes_the_bytes(self):
        """The copy holds what was handed over."""
        with tempfile.TemporaryDirectory() as directory:
            stored = Path(directory, "book.xlsx.mtsv")
            _cache.store(stored, b"a\n")
            self.assertEqual(stored.read_bytes(), b"a\n")

    def test_makes_the_folders(self):
        """Folders that do not exist yet are made."""
        with tempfile.TemporaryDirectory() as directory:
            stored = Path(directory, "home", "me", "book.xlsx.mtsv")
            _cache.store(stored, b"a\n")
            self.assertTrue(stored.exists())

    def test_replaces_an_older_copy(self):
        """A second copy takes the place of the first."""
        with tempfile.TemporaryDirectory() as directory:
            stored = Path(directory, "book.xlsx.mtsv")
            _cache.store(stored, b"a\n")
            _cache.store(stored, b"b\n")
            self.assertEqual(stored.read_bytes(), b"b\n")

    def test_leaves_nothing_beside_it(self):
        """Nothing but the copy is left where it was written."""
        with tempfile.TemporaryDirectory() as directory:
            stored = Path(directory, "book.xlsx.mtsv")
            _cache.store(stored, b"a\n")
            self.assertEqual(
                [path.name for path in Path(directory).iterdir()],
                ["book.xlsx.mtsv"],
            )
