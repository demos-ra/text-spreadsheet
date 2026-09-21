"""Run the text-spreadsheet server.

Functions:
main -- run the server on standard input and output
"""

__all__ = ["main"]

from text_spreadsheet import _server


def main() -> None:
    """Run the server on standard input and output.

    MCP Python SDK, Running your server: mcp.run() with no argument
    starts a stdio server, which blocks.
    """
    _server.mcp.run()


if __name__ == "__main__":
    main()
