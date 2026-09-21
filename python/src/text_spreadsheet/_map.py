"""What a file is made of: its sheets, their columns, and what was left.

Functions:
of -- return the map of a file as MTSV sheets
"""

__all__ = ["of"]

from pathlib import Path
from typing import Any

# The draft, Generators: "A generator MUST write an FF line before
# every sheet, including the first", so a sheet takes that line, then
# its header, then one line per record.
_FF_LINE = 1


def of(
    sheets: list[dict[str, Any]],
    source: Path,
    stored: Path,
    converted: bool,
    left_behind: list[str],
) -> list[dict[str, Any]]:
    """Return the map of a file as MTSV sheets.

    sheets -- the sheets the file holds
    source -- the path that was read
    stored -- the path of the MTSV copy
    converted -- whether this call converted the file
    left_behind -- the names the conversion reported, as reported

    Return four sheets: file, sheets, columns and left behind.
    """
    return [
        _file(source, stored, converted),
        _sheets(sheets),
        _columns(sheets),
        _left_behind(left_behind),
    ]


def _file(source: Path, stored: Path, converted: bool) -> dict[str, Any]:
    """Return the sheet naming the file and its copy."""
    return {
        "sheet name": "file",
        "header": ["source", "artifact", "converted"],
        "records": [[str(source), str(stored), "yes" if converted else "no"]],
    }


def _sheets(sheets: list[dict[str, Any]]) -> dict[str, Any]:
    """Return the sheet naming each sheet, its records and its lines.

    The draft, Data Model: a sheet is a header and an ordered sequence
    of records, so how many records it holds is what the rows address
    counts.
    """
    rows = []
    line = 1
    for number, sheet in enumerate(sheets, 1):
        last = line + _FF_LINE + _lines(sheet) - 1
        rows.append(
            [
                str(number),
                sheet["sheet name"],
                str(len(sheet["records"])),
                str(line),
                str(last),
            ]
        )
        line = last + 1
    return {
        "sheet name": "sheets",
        "header": ["sheet", "sheet name", "records", "first line", "last line"],
        "records": rows,
    }


def _columns(sheets: list[dict[str, Any]]) -> dict[str, Any]:
    """Return the sheet naming each column and its position."""
    records = []
    for number, sheet in enumerate(sheets, 1):
        for position, name in enumerate(sheet["header"] or [], 1):
            records.append([str(number), str(position), name])
    return {
        "sheet name": "columns",
        "header": ["sheet", "position", "field name"],
        "records": records,
    }


def _left_behind(names: list[str]) -> dict[str, Any]:
    """Return the sheet naming what the conversion left behind."""
    return {
        "sheet name": "left behind",
        "header": ["what"],
        "records": [[name] for name in names],
    }


def _lines(sheet: dict[str, Any]) -> int:
    """Return how many lines a sheet takes after its FF line."""
    if sheet["header"] is None:
        return 0
    return 1 + len(sheet["records"])
