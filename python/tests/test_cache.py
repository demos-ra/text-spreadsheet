"""Test text_spreadsheet._cache: platformdirs, RFC 9111, POSIX."""

import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from text_spreadsheet import _cache

import support

TEXT = "\fPeople\nName\nAda\n"


class TestArtifact(unittest.TestCase):
    """artifact: where the MTSV copy of a source file is kept."""

    def test_asks_platformdirs(self):
        """platformdirs: user_cache_dir, appname, appauthor False."""
        _cache.artifact(Path("/home/me/book.xlsx"))
        support.user_cache_dir.assert_called_with("text-spreadsheet", appauthor=False)

    def test_under_the_cache_directory(self):
        """The copy sits under the user's cache directory."""
        path = _cache.artifact(Path("/home/me/book.xlsx"))
        self.assertEqual(path.parts[: len(support.CACHE.parts)], support.CACHE.parts)

    def test_mirrors_the_source_path(self):
        """The source path is mirrored, with MTSV added to the name."""
        self.assertEqual(
            _cache.artifact(Path("/home/me/book.xlsx")),
            support.CACHE / "home/me/book.xlsx.mtsv",
        )

    def test_two_folders_do_not_collide(self):
        """One name in two folders gives two copies."""
        self.assertNotEqual(
            _cache.artifact(Path("/home/me/book.xlsx")),
            _cache.artifact(Path("/home/you/book.xlsx")),
        )

    def test_the_whole_name_is_kept(self):
        """Whatever the format, the copy is MTSV; two never collide."""
        names = ("book.xlsx", "book.ods", "book.sqlite", "book.parquet")
        paths = [_cache.artifact(Path("/home/me", name)) for name in names]
        self.assertEqual(len(set(paths)), len(names))
        for name, path in zip(names, paths):
            with self.subTest(name):
                self.assertEqual(path.name, name + ".mtsv")


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
                sorted(path.name for path in Path(directory).iterdir()),
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

    def test_makes_the_folders(self):
        """Folders that do not exist yet are made."""
        with tempfile.TemporaryDirectory() as directory:
            stored = Path(directory, "home", "me", "book.xlsx.mtsv")
            _cache.store(stored, TEXT, [])
            self.assertTrue(stored.exists())

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
                sorted(path.name for path in Path(directory).iterdir()),
                ["book.xlsx.mtsv", "book.xlsx.mtsv-metadata.mtsv"],
            )

    def test_working_name_is_the_process_and_thread(self):
        """POSIX 1.4: two writers write under two working names."""
        with tempfile.TemporaryDirectory() as directory:
            stored = Path(directory, "book.xlsx.mtsv")
            written = []
            original = Path.write_bytes

            def spy(path, data):
                written.append(path.name)
                return original(path, data)

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

    def test_source_newer(self):
        """A source changed after its copy is stale."""
        with tempfile.TemporaryDirectory() as directory:
            stored = Path(directory, "book.xlsx.mtsv")
            _cache.store(stored, TEXT, [])
            os.utime(stored, (0, 0))
            self.assertFalse(_cache.is_fresh(stored, 1))
