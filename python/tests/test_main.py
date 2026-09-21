"""Test text_spreadsheet.__main__: the entry point of the server."""

import unittest
from unittest import mock

from text_spreadsheet import __main__


class TestMain(unittest.TestCase):
    """main: the command a host launches."""

    def test_runs_the_server(self):
        """main runs the server, which takes the transport it finds."""
        with mock.patch("text_spreadsheet._server.mcp.run") as run:
            __main__.main()
        run.assert_called_once_with()
