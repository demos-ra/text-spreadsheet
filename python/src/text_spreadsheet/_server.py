"""The server a host launches, and the tool it offers.

Objects:
mcp -- the server

Functions:
read -- read spreadsheets as text, every sheet at once
"""

__all__ = ["mcp", "read"]

from importlib.metadata import metadata

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

import text_spreadsheet
from text_spreadsheet import _refusal

# MCP, schema Implementation: name, title, version, description and
# websiteUrl describe the server.
_NAME = "text-spreadsheet"
_TITLE = "Text Spreadsheet"
_PACKAGE = metadata(_NAME)
_ENTRIES = [entry.split(",", 1) for entry in _PACKAGE.get_all("Project-URL")]
_URLS = {label.strip(): address.strip() for label, address in _ENTRIES}

mcp = MCPServer(
    _NAME,
    title=_TITLE,
    description=_PACKAGE["Summary"],
    website_url=_URLS["source"],
    version=_PACKAGE["Version"],
)


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
    filter: str | None = None,
) -> str:
    """Read spreadsheets as text, every sheet at once.

    MTSV, JSON, Excel, ODS, CSV, SQLite, Parquet and Arrow files, or a
    folder of them. With a path alone, return a map: the files, their
    sheets, how many records each holds and how many the filter keeps,
    the columns of each, where each sheet's lines are, and what the
    conversion left behind. Add a position to return that part instead.

    The reply is tab-separated text: a tab between fields, a line break
    between records, and a form feed before each sheet's name.

    path -- the absolute path of a file, or of a folder of files
    sheet -- which sheets, as 2, 1;3, 1-3 or 2-*, counting from 1
    rows -- which records of each sheet, written the same way
    fields -- which fields of each record, written the same way
    filter -- which records to keep, as an RFC 9535 filter such as
        @[1] == 'open' && search(@[2], 'x')

    A folder is read without its subfolders and without names that
    begin with a dot, in name order; its sheets are numbered across
    its files. A file with no format, or one that cannot be read, and
    a subfolder or anything else that is not a regular file, skipped,
    are named in the map, and the others are still read.

    Positions that do not exist are left out, and a sheet left with no
    field comes back empty. rows counts the records the filter keeps.
    In a filter, @[0] is a record's first field, the same position in
    every sheet the call chooses; text is compared exactly; match()
    tests a whole field and search() any part of it, with patterns in
    I-Regexp: [0-9], not \\d, and a backslash written twice.

    The path must be absolute. A file named directly that cannot be
    read or converted, a folder that cannot be listed, an extension
    this server has no format for, and an address or filter not
    written as its syntax writes one are each refused with the reason.
    A file holding a tab or line break inside a value cannot be
    converted.

    A copy of each converted file is kept as MTSV under the cache
    directory where one can be written, with what it left behind beside
    it, and the map names where, so it can be read directly afterwards.
    """
    try:
        return text_spreadsheet.read(
            path, sheet=sheet, rows=rows, fields=fields, filter=filter
        )
    except _refusal.RefusalError as error:
        raise ToolError(str(error)) from error
