"""Test text_spreadsheet._server against the MCP Python SDK."""

import asyncio
import shutil
import tempfile
import unittest
from importlib.metadata import version
from pathlib import Path

import mtsv
from mcp.server.mcpserver.exceptions import ToolError, UnexpectedToolError
from mcp.types import ToolAnnotations
from mtsv.integrations import xlsx

from text_spreadsheet import _cache, _server

import support

SHEETS = [{"sheet name": "People", "header": ["Name"], "records": [["Ada"]]}]


def published(name):
    """Return a tool as a host lists it."""
    tools = asyncio.run(_server.mcp.list_tools())
    return next(one for one in tools if one.name == name)


class TestServer(unittest.TestCase):
    """mcp: the server a host launches."""

    def test_named_for_the_package(self):
        """The server carries the name a host lists it under."""
        self.assertEqual(_server.mcp.name, "text-spreadsheet")

    def test_describes_itself(self):
        """MCP, schema Implementation: title, version and website."""
        self.assertEqual(_server.mcp.title, "Text Spreadsheet")
        self.assertEqual(_server.mcp.version, version("text-spreadsheet"))
        self.assertEqual(
            _server.mcp.website_url, "https://github.com/demos-ra/text-spreadsheet"
        )


class TestRead(unittest.TestCase):
    """read: the tool the server offers."""

    def setUp(self):
        """Collect the copies to remove."""
        self.stored = []

    def tearDown(self):
        """Remove the copies the test left in the cache."""
        for path in self.stored:
            shutil.rmtree(path.parent, ignore_errors=True)

    def test_describes_itself(self):
        """The description is the docstring, as the SDK derives it."""
        self.assertTrue(_server.read.__doc__.startswith("Read spreadsheets"))

    def test_no_structured_content(self):
        """No output schema is published, so the reply is the text."""
        self.assertIsNone(published("read").output_schema)

    def test_publishes_its_annotations(self):
        """The hints are published as the tool declares them."""
        self.assertEqual(
            published("read").annotations,
            ToolAnnotations(
                read_only_hint=False,
                destructive_hint=False,
                idempotent_hint=True,
                open_world_hint=False,
            ),
        )

    def test_maps_a_file(self):
        """A path alone gives the map of the file."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "book.xlsx")
            with path.open("wb") as fp:
                xlsx.dump(SHEETS, fp)
            self.stored.append(_cache.artifact(path))
            names = [
                sheet["sheet name"] for sheet in mtsv.loads(_server.read(str(path)))
            ]
            self.assertEqual(names, ["file", "sheets", "columns", "left behind"])

    def test_takes_a_filter(self):
        """The published schema offers the filter parameter."""
        self.assertIn("filter", published("read").input_schema["properties"])

    def test_a_refusal_carries_its_reason(self):
        """MCP, server/tools Error Handling: the reason is read."""
        with self.assertRaises(ToolError) as caught:
            _server.read("book.xlsx")
        self.assertIn("absolute", str(caught.exception))

    def test_a_refusal_reaches_the_model(self):
        """Through the SDK, a refusal is anticipated, not a crash."""
        with self.assertRaises(ToolError) as caught:
            asyncio.run(_server.mcp.call_tool("read", {"path": "x"}))
        self.assertNotIsInstance(caught.exception, UnexpectedToolError)
        self.assertIn("absolute", str(caught.exception))

    def test_an_address_names_a_part(self):
        """An address gives that part of the file, not the map."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "book.xlsx")
            with path.open("wb") as fp:
                xlsx.dump(SHEETS, fp)
            self.stored.append(_cache.artifact(path))
            text = _server.read(str(path), sheet="1")
            self.assertEqual(mtsv.loads(text), SHEETS)
