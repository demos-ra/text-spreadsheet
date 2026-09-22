"""The server a host launches, and the tool it offers.

Objects:
mcp -- the server

Functions:
read -- read a spreadsheet as text, every sheet at once
"""

__all__ = ["mcp", "read"]

from mcp.server import MCPServer
from mcp.types import ToolAnnotations

import text_spreadsheet

mcp = MCPServer("text-spreadsheet")


# MCP, schema ToolAnnotations: "additional properties describing a Tool
# to clients", each a hint.
# MCP, server/tools Structured Content: "a tool that returns structured
# content SHOULD also return the serialized JSON in a TextContent
# block".
@mcp.tool(
    annotations=ToolAnnotations(
        read_only_hint=False,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=False,
    ),
    structured_output=False,
)
def read(
    path: str,
    sheet: str | None = None,
    rows: str | None = None,
    fields: str | None = None,
) -> str:
    """Read a spreadsheet as text, every sheet at once.

    Excel, ODS, CSV, SQLite, Parquet and Arrow files. With a path
    alone, return a map of the file: its sheets, how many records each
    holds, the columns of each, where each sheet's lines are, and what
    the conversion left behind. Add an address to return that part of
    the file instead.

    The reply is tab-separated text: a tab between fields, a line break
    between records, and a form feed before each sheet's name.

    path -- the absolute path of the file to read
    sheet -- which sheets, as 2, 1;3 or 1-3, counting from 1
    rows -- which records of each sheet, written the same way
    fields -- which fields of each record, written the same way

    The path must be absolute. A file that cannot be read, an
    extension this server has no format for, and an address the file
    does not have are each refused rather than guessed.

    A copy of the file is kept as MTSV under the cache directory, and
    the map names where, so it can be read directly afterwards.
    """
    return text_spreadsheet.read(path, sheet=sheet, rows=rows, fields=fields)
