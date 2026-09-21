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


# MCP, schema ToolAnnotations: readOnlyHint is false because the tool
# writes the copy; destructiveHint false because it only adds;
# idempotentHint true because the same arguments write the same copy;
# openWorldHint false because a file system is a closed domain.
@mcp.tool(
    annotations=ToolAnnotations(
        read_only_hint=False,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=False,
    )
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

    A copy of the file is kept as MTSV under the cache directory, and
    the map names where, so it can be read directly afterwards.
    """
    return text_spreadsheet.read(path, sheet=sheet, rows=rows, fields=fields)
