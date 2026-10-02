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
    pathname: str,
    sheet: str | None = None,
    records: str | None = None,
    fields: str | None = None,
    filter: str | None = None,
) -> str:
    """Read spreadsheets as text, every sheet at once.

    Excel, ODS, CSV, JSON, SQLite, Parquet, Arrow and MTSV files, or a
    directory of them. Every reply begins with the report, four sheets:
    file, each file and its pathname; not read, each file not read and
    why; left behind, what each conversion lost; and sheets, each sheet
    chosen with how many records it holds, how many the filter keeps,
    and the positions of the records named. Then, with a pathname
    alone, the map: the fields of each sheet. With a selection, those
    values instead.

    The reply is tab-separated text: a tab between fields, a line break
    between records, and a form feed before each sheet's name.

    pathname -- the absolute pathname of a file, or of a directory
    sheet -- which sheets of each file, as 2, 1;3, 1-3 or 2-*,
        counting from 1
    records -- which records of each sheet, written the same way
    fields -- which fields of each record, written the same way
    filter -- which records to keep, as an RFC 9535 filter such as
        @[1] == 'open' && search(@[2], 'x')

    A directory is read without the directories within it and without
    names that begin with a dot, in name order. A file with no format,
    one that cannot be read, and anything that is not a regular file,
    skipped, are named in not read, and the others are still read.

    Positions that do not exist are left out, and a sheet left with no
    field comes back empty. records counts the records the filter
    keeps. In a filter, @[0] is a record's first field, the same
    position in every sheet the call chooses; text is compared exactly;
    match() tests a whole field and search() any part of it, with
    patterns in I-Regexp: [0-9], not \\d, and a backslash written
    twice.

    The pathname must be absolute. A file named directly that cannot be
    read, has no format, cannot be converted, or whose name holds a tab
    or line break, a pathname that names neither a directory nor a
    regular file, a directory that cannot be listed, and a selection or
    filter not written as its syntax writes one are each refused with
    the reason.
    """
    try:
        return text_spreadsheet.read(
            pathname, sheet=sheet, records=records, fields=fields, filter=filter
        )
    except _refusal.RefusalError as error:
        raise ToolError(str(error)) from error
