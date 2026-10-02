"""Test text_spreadsheet.read: the reply, and each cell of the grid.

The grid is the register's: each level, directory, file, sheet, record
and field, with each outcome, stated the same by the map and by the
values.

Classes:
TestReply -- read: the report, then the answer
TestDirectory -- read: the directory, with each outcome
TestFile -- read: the file, with each outcome
TestSheet -- read: the sheet, with each outcome
TestRecord -- read: the record, with each outcome
TestField -- read: the field, with each outcome
TestCall -- read: a call that gets no reply
TestCopy -- read: the copy of a converted file
"""

__all__ = [
    "TestReply",
    "TestDirectory",
    "TestFile",
    "TestSheet",
    "TestRecord",
    "TestField",
    "TestCall",
    "TestCopy",
]

import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import mtsv
from mtsv.integrations import xlsx

from text_spreadsheet import _cache, read

import support

PEOPLE = [
    {
        "sheet name": "People",
        "header": ["Name", "Town"],
        "records": [["Ada", "Ely"], ["Bo", "Rye"], ["Cy", "Ely"]],
    }
]
OTHER = [{"sheet name": "Other", "header": ["Name"], "records": [["Bo"]]}]
LOSES = b'[{"sheet name":"S","header":["a"],"records":[["1"]],"x":1}]'
BREAKS = b'[{"sheet name":"","header":["a"],"records":[["b\\nc"]]}]'
REPORT = ["file", "not read", "left behind", "sheets"]
MAP = {}
VALUES = {"sheet": "1"}
BOTH = (("the map", MAP), ("the values", VALUES))


def report(text):
    """Return the four sheets that begin a reply, by sheet name."""
    return {sheet["sheet name"]: sheet["records"] for sheet in mtsv.loads(text)[:4]}


def answer(text):
    """Return the sheets of a reply after its report."""
    return mtsv.loads(text)[4:]


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

    def write(self, name, value=PEOPLE):
        """Write sheets, or bytes, to a file in the directory."""
        pathname = self.directory / name
        with pathname.open("wb") as fp:
            if isinstance(value, bytes):
                fp.write(value)
            elif pathname.suffix == ".mtsv":
                mtsv.dump(value, fp)
            else:
                xlsx.dump(value, fp)
        return pathname

    def fill(self):
        """Write a member of each kind, and return the directory."""
        self.write("a.mtsv")
        self.write("b.json", LOSES)
        self.write("c.txt", b"x\n")
        (self.directory / "d").mkdir()
        self.write("e.json", BREAKS)
        return str(self.directory)


class TestReply(Directory):
    """read: the report, then the answer."""

    def test_the_report_begins_every_reply(self):
        """Four sheets, from big to small, whatever the call."""
        pathname = str(self.write("a.mtsv"))
        for name, selection in BOTH:
            with self.subTest(name):
                text = read(pathname, **selection)
                names = [sheet["sheet name"] for sheet in mtsv.loads(text)]
                self.assertEqual(names[:4], REPORT)

    def test_the_report_is_the_same_for_both(self):
        """The map and the values of one selection report alike."""
        directory = self.fill()
        for filter in (None, "@[0] == 'Ada'"):
            with self.subTest(filter):
                scan = report(read(directory, filter=filter))
                pull = report(read(directory, sheet="1", filter=filter))
                self.assertEqual(scan, pull)

    def test_the_map_answers_with_fields(self):
        """No selection: the names of the fields of each sheet."""
        text = read(str(self.write("a.mtsv")))
        self.assertEqual(
            answer(text),
            [
                {
                    "sheet name": "fields",
                    "header": ["file", "sheet", "field", "field name"],
                    "records": [["1", "1", "1", "Name"], ["1", "1", "2", "Town"]],
                }
            ],
        )

    def test_the_values_answer_with_the_sheets(self):
        """A selection: each file's chosen sheets in turn."""
        self.write("a.mtsv")
        self.write("b.mtsv", OTHER)
        self.assertEqual(answer(read(str(self.directory), sheet="1")), PEOPLE + OTHER)

    def test_nothing_to_state(self):
        """With nothing to state, a report sheet holds no record."""
        pathname = str(self.write("a.mtsv"))
        for name, selection in BOTH:
            with self.subTest(name):
                stated = report(read(pathname, **selection))
                self.assertEqual((stated["not read"], stated["left behind"]), ([], []))


class TestDirectory(Directory):
    """read: the directory, with each outcome."""

    def test_came_back(self):
        """file names every member, read or not, with its source."""
        directory = self.fill()
        for name, selection in BOTH:
            with self.subTest(name):
                self.assertEqual(
                    report(read(directory, **selection))["file"],
                    [
                        [str(n), str(self.directory / member)]
                        for n, member in enumerate(
                            ("a.mtsv", "b.json", "c.txt", "d", "e.json"), 1
                        )
                    ],
                )

    def test_no_members(self):
        """An empty directory is answered: a report with no record."""
        for name, selection in BOTH:
            with self.subTest(name):
                text = read(str(self.directory), **selection)
                self.assertEqual(list(report(text).values()), [[], [], [], []])

    def test_none_read(self):
        """A directory of directories: the report, nothing chosen."""
        (self.directory / "2026").mkdir()
        for name, selection in BOTH:
            with self.subTest(name):
                stated = report(read(str(self.directory), **selection))
                self.assertEqual(stated["not read"], [["1", "skipped: directory"]])
                self.assertEqual(stated["sheets"], [])
        self.assertEqual(answer(read(str(self.directory), sheet="1")), [])

    def test_cannot_be_listed(self):
        """A directory that cannot be listed is refused."""
        for name, selection in BOTH:
            with self.subTest(name):
                with mock.patch("os.scandir", side_effect=PermissionError("no")):
                    with self.assertRaises(OSError):
                        read(str(self.directory), **selection)


class TestFile(Directory):
    """read: the file, with each outcome."""

    def test_came_back(self):
        """A file read is in file, and not in not read."""
        pathname = str(self.write("a.mtsv"))
        for name, selection in BOTH:
            with self.subTest(name):
                stated = report(read(pathname, **selection))
                self.assertEqual(stated["file"], [["1", pathname]])
                self.assertEqual(stated["not read"], [])

    def test_a_member_not_read(self):
        """Each member not read is named with its status."""
        directory = self.fill()
        for name, selection in BOTH:
            with self.subTest(name):
                not_read = report(read(directory, **selection))["not read"]
                self.assertEqual(
                    [(file, status.split(":")[0]) for file, status in not_read],
                    [("3", "no format"), ("4", "skipped"), ("5", "failed")],
                )

    def test_lost_something(self):
        """A loss is named with its file."""
        directory = self.fill()
        for name, selection in BOTH:
            with self.subTest(name):
                stated = report(read(directory, **selection))
                self.assertEqual(stated["left behind"], [["2", "x"]])

    def test_named_directly_and_not_readable(self):
        """A file named directly that cannot be read is refused."""
        os.mkfifo(self.directory / "pipe.mtsv")
        cases = (
            ("absent.xlsx", OSError),
            ("pipe.mtsv", OSError),
            (self.write("c.txt", b"x\n").name, LookupError),
            (self.write("e.json", BREAKS).name, ValueError),
            (self.write("a\tb.mtsv").name, ValueError),
        )
        for member, error in cases:
            for name, selection in BOTH:
                with self.subTest(member=member, call=name):
                    with self.assertRaises(error):
                        read(str(self.directory / member), **selection)


class TestSheet(Directory):
    """read: the sheet, with each outcome."""

    def test_came_back(self):
        """sheets names each sheet chosen: its file, position, name."""
        directory = self.fill()
        for name, selection in BOTH:
            with self.subTest(name):
                sheets = report(read(directory, **selection))["sheets"]
                self.assertEqual(
                    [line[:3] for line in sheets],
                    [["1", "1", "People"], ["2", "1", "S"]],
                )

    def test_does_not_exist(self):
        """A sheet a file does not have is left out, with no record."""
        text = read(self.fill(), sheet="2")
        self.assertEqual(report(text)["sheets"], [])
        self.assertEqual(answer(text), [])


class TestRecord(Directory):
    """read: the record, with each outcome."""

    def test_how_many_and_how_many_match(self):
        """records counts the sheet, matches what the filter keeps."""
        pathname = str(self.write("a.xlsx"))
        for name, selection in BOTH:
            with self.subTest(name):
                text = read(pathname, filter="@[1] == 'Ely'", **selection)
                self.assertEqual(report(text)["sheets"][0][3:5], ["3", "2"])

    def test_matches_without_a_filter(self):
        """With no filter, every record matches."""
        pathname = str(self.write("a.mtsv"))
        for name, selection in BOTH:
            with self.subTest(name):
                sheets = report(read(pathname, **selection))["sheets"]
                self.assertEqual(sheets[0][3:5], ["3", "3"])

    def test_came_back(self):
        """The values hold the records, and positions names them."""
        pathname = str(self.write("a.mtsv"))
        cases = (
            ({"sheet": "1"}, "1-3", [["Ada", "Ely"], ["Bo", "Rye"], ["Cy", "Ely"]]),
            ({"records": "3;1"}, "3;1", [["Cy", "Ely"], ["Ada", "Ely"]]),
            ({"records": "2", "filter": "@[1] == 'Ely'"}, "3", [["Cy", "Ely"]]),
        )
        for selection, positions, records in cases:
            with self.subTest(positions):
                text = read(pathname, **selection)
                self.assertEqual(report(text)["sheets"][0][5], positions)
                self.assertEqual(answer(text)[0]["records"], records)

    def test_positions_can_be_given_back(self):
        """What positions holds, given as records, names the same."""
        pathname = str(self.write("a.mtsv"))
        first = read(pathname, sheet="1", filter="@[1] == 'Ely'")
        again = read(pathname, sheet="1", records=report(first)["sheets"][0][5])
        self.assertEqual(answer(again), answer(first))

    def test_named_by_the_map(self):
        """The map names the records a filter keeps, and holds none."""
        text = read(str(self.write("a.mtsv")), filter="@[1] == 'Ely'")
        self.assertEqual(report(text)["sheets"][0][3:], ["3", "2", "1;3"])
        self.assertEqual([sheet["sheet name"] for sheet in answer(text)], ["fields"])

    def test_does_not_exist(self):
        """A record past the size is left out; records is the size."""
        text = read(str(self.write("a.mtsv")), records="9")
        self.assertEqual(report(text)["sheets"][0][3:], ["3", "3", ""])
        self.assertEqual(
            answer(text),
            [{"sheet name": "People", "header": ["Name", "Town"], "records": []}],
        )

    def test_not_kept_by_the_filter(self):
        """A record the filter does not keep is left out."""
        text = read(str(self.write("a.mtsv")), sheet="1", filter="@[0] == 'Bo'")
        self.assertEqual(answer(text)[0]["records"], [["Bo", "Rye"]])
        self.assertEqual(report(text)["sheets"][0][3:], ["3", "1", "2"])


class TestField(Directory):
    """read: the field, with each outcome."""

    def test_came_back(self):
        """The map names each field; the values' header holds them."""
        pathname = str(self.write("a.mtsv"))
        with self.subTest("the map"):
            fields = answer(read(pathname))[0]["records"]
            self.assertEqual(fields, [["1", "1", "1", "Name"], ["1", "1", "2", "Town"]])
        with self.subTest("the values"):
            part = answer(read(pathname, fields="2"))[0]
            self.assertEqual((part["header"], part["records"][0]), (["Town"], ["Ely"]))

    def test_does_not_exist(self):
        """A sheet left with no field comes back empty, as MTSV."""
        text = read(str(self.write("a.mtsv")), fields="9")
        self.assertEqual(
            answer(text), [{"sheet name": "People", "header": None, "records": []}]
        )
        self.assertEqual(report(text)["sheets"][0][3:], ["3", "3", "1-3"])

    def test_across_widths(self):
        """Each sheet of the group keeps the fields it has."""
        self.write("a.mtsv")
        self.write("b.mtsv", OTHER)
        text = read(str(self.directory), fields="2")
        self.assertEqual([part["header"] for part in answer(text)], [["Town"], None])

    def test_holds_what_mtsv_cannot(self):
        """A value MTSV cannot hold: the member is not read."""
        directory = self.fill()
        for name, selection in BOTH:
            with self.subTest(name):
                not_read = report(read(directory, **selection))["not read"]
                self.assertTrue(not_read[-1][1].startswith("failed: "))


class TestCall(Directory):
    """read: a call that gets no reply."""

    def test_not_written_as_its_syntax_writes_it(self):
        """A pathname, selection or filter not as written: refused."""
        pathname = str(self.write("a.mtsv"))
        cases = (
            ("a relative pathname", "a.mtsv", {}),
            ("a selection", pathname, {"records": "1,2"}),
            ("a filter", pathname, {"filter": "@[0] = 'x'"}),
        )
        for case, given, wrong in cases:
            for name, selection in BOTH:
                with self.subTest(case=case, call=name):
                    with self.assertRaises(ValueError):
                        read(given, **{**selection, **wrong})

    def test_a_fault(self):
        """An error that is not a refusal is not answered as one."""
        directory = self.fill()
        for name, selection in BOTH:
            with self.subTest(name):
                with mock.patch(
                    "text_spreadsheet._conversion.of", side_effect=KeyError("k")
                ):
                    with self.assertRaises(KeyError):
                        read(directory, **selection)


class TestCopy(Directory):
    """read: the copy of a converted file."""

    def test_serves_the_copy(self):
        """A file no newer than its copy is not converted again."""
        pathname = self.write("book.xlsx")
        read(str(pathname))
        with _cache.location(pathname).open("wb") as fp:
            mtsv.dump(OTHER, fp)
        self.assertEqual(report(read(str(pathname)))["sheets"][0][2], "Other")

    def test_converts_again_when_the_file_changes(self):
        """A file newer than its copy is converted again."""
        pathname = self.write("book.xlsx")
        read(str(pathname))
        with _cache.location(pathname).open("wb") as fp:
            mtsv.dump(OTHER, fp)
        os.utime(_cache.location(pathname), (0, 0))
        self.assertEqual(report(read(str(pathname)))["sheets"][0][2], "People")
