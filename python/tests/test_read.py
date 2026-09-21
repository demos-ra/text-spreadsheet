"""Test read against the addressing and the formats that govern it.

Each case that confirms a rule names its section: RFC 8089 for the
file URI scheme, RFC 3986 for the generic URI syntax.
"""

import tempfile
import unittest
from pathlib import Path

import mtsv
from mtsv.integrations import xlsx

from text_spreadsheet import read

SHEETS = [
    {"sheet name": "People", "header": ["Name"], "records": [["Ada"]]}
]


def written(directory, name):
    """Write the sheets to a file in a directory, and return it."""
    path = Path(directory, name)
    with path.open("wb") as fp:
        if path.suffix == ".mtsv":
            mtsv.dump(SHEETS, fp)
        else:
            xlsx.dump(SHEETS, fp)
    return path


class TestRead(unittest.TestCase):
    """Reading a file that a URI identifies."""

    def test_reads_mtsv(self):
        """The extension .mtsv reads through the parser itself."""
        with tempfile.TemporaryDirectory() as directory:
            path = written(directory, "book.mtsv")
            self.assertEqual(read(path.as_uri()), SHEETS)

    def test_reads_a_spreadsheet(self):
        """An extension of an integration reads through it."""
        with tempfile.TemporaryDirectory() as directory:
            path = written(directory, "book.xlsx")
            self.assertEqual(read(path.as_uri()), SHEETS)

    def test_errors_reaches_the_integration(self):
        """The errors value is the integration's, not a new one."""
        with tempfile.TemporaryDirectory() as directory:
            path = written(directory, "book.xlsx")
            with self.assertRaises(LookupError):
                read(path.as_uri(), errors="replace")

    def test_extension_must_name_a_format(self):
        """A name with no extension names no format, so it stops.

        Every format is named by the extension its media type
        registration declares, so a name that carries no extension
        can never name one.
        """
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "book")
            path.write_bytes(b"a\n")
            with self.assertRaises(LookupError):
                read(path.as_uri())


class TestAddress(unittest.TestCase):
    """The file URI syntax of RFC 8089, Sections 2 to 4."""

    def test_percent_encoded_path(self):
        """Section 4: the path is UTF-8, then percent-encoded."""
        with tempfile.TemporaryDirectory() as directory:
            path = written(directory, "my book.mtsv")
            uri = path.as_uri()
            self.assertIn("%20", uri)
            self.assertEqual(read(uri), SHEETS)

    def test_localhost_authority_is_local(self):
        """Section 3: the authority "localhost" is this machine."""
        with tempfile.TemporaryDirectory() as directory:
            path = written(directory, "book.mtsv")
            uri = path.as_uri().replace("file://", "file://localhost", 1)
            self.assertEqual(read(uri), SHEETS)

    def test_scheme_must_be_file(self):
        """Section 2: the scheme of a file URI is "file"."""
        with self.assertRaises(ValueError):
            read("https://example.com/book.mtsv")

    def test_authority_must_be_local(self):
        """Section 3: a non-local file URI has no local path."""
        with self.assertRaises(ValueError):
            read("file://example.com/book.mtsv")

    def test_path_must_be_absolute(self):
        """Section 2: local-path is the path-absolute rule."""
        with self.assertRaises(ValueError):
            read("file:book.mtsv")

    def test_query_is_refused(self):
        """Section 2: file-hier-part carries no query."""
        with self.assertRaises(ValueError):
            read("file:///book.mtsv?sheet=People")

    def test_fragment_is_refused(self):
        """Section 2: file-hier-part carries no fragment."""
        with self.assertRaises(ValueError):
            read("file:///book.mtsv#People")
