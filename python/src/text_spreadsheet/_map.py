"""What a group of files is made of: its files, sheets, columns, losses.

Functions:
of -- return the map of a selection as MTSV sheets
"""

__all__ = ["of"]

from typing import Any

from text_spreadsheet import _field

_FF = "\f"
_LF = "\n"
_SIGNATURE = "﻿"

_YES = "yes"
_NO = "no"


def of(
    group: list[dict[str, Any]], selection: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Return the map of a selection as MTSV sheets.

    group -- the files of the call, as the input named them
    selection -- the sheets of the call, as they were selected

    Return four sheets: file, sheets, columns and left behind.
    """
    lines = {file["file"]: _lines(file["text"]) for file in group}
    return [
        _files(group),
        _sheets(selection, lines),
        _columns(selection),
        _left_behind(group),
    ]


def _files(group: list[dict[str, Any]]) -> dict[str, Any]:
    """Return the sheet naming each file, its artifact, and its status.

    group -- the files of the call

    A file with no artifact has an empty field. CSVW, 4.5 Cells: an
    empty string value is read as null.
    """
    return {
        "sheet name": "file",
        "header": ["file", "source", "artifact", "converted", "status"],
        "records": [
            [
                str(file["file"]),
                _field.written(str(file["source"])),
                (
                    ""
                    if file["artifact"] is None
                    else _field.written(str(file["artifact"]))
                ),
                _YES if file["converted"] else _NO,
                file["status"],
            ]
            for file in group
        ],
    }


def _sheets(
    selection: list[dict[str, Any]], lines: dict[int, list[tuple[int, int]]]
) -> dict[str, Any]:
    """Return the sheet naming each sheet, its counts, and its lines.

    selection -- the sheets of the call
    lines -- the first and last line of each sheet, by file

    CSVW, 4.4 Rows: a row has a number among the rows selected and a
    source number in the original; records counts the sheet, matches
    what the condition keeps.
    """
    records = []
    for entry in selection:
        first, last = lines[entry["file"]][entry["position in file"] - 1]
        records.append(
            [
                str(entry["sheet"]),
                str(entry["file"]),
                entry["part"]["sheet name"],
                str(entry["records"]),
                str(entry["matches"]),
                str(first),
                str(last),
            ]
        )
    return {
        "sheet name": "sheets",
        "header": [
            "sheet",
            "file",
            "sheet name",
            "records",
            "matches",
            "first line",
            "last line",
        ],
        "records": records,
    }


def _columns(selection: list[dict[str, Any]]) -> dict[str, Any]:
    """Return the sheet naming each column and its position.

    selection -- the sheets of the call
    """
    records = []
    for entry in selection:
        for position, name in enumerate(entry["part"]["header"] or [], 1):
            records.append([str(entry["sheet"]), str(position), name])
    return {
        "sheet name": "columns",
        "header": ["sheet", "position", "field name"],
        "records": records,
    }


def _left_behind(group: list[dict[str, Any]]) -> dict[str, Any]:
    """Return the sheet naming what each conversion left behind.

    group -- the files of the call

    CSVW, 4.2 Tables: notes are annotations on the table they concern.
    """
    return {
        "sheet name": "left behind",
        "header": ["file", "what"],
        "records": [
            [str(file["file"]), name] for file in group for name in file["left behind"]
        ],
    }


def _lines(text: str) -> list[tuple[int, int]]:
    """Return the first and last line of each sheet in an MTSV text.

    text -- the MTSV text of one file

    The draft, Parsers: the lines before the first FF, if any, are the
    first sheet, and each line that begins with an FF starts a new
    sheet; a U+FEFF at the start of a file is an encoding signature.
    """
    lines = text.split(_LF)
    if lines and lines[-1] == "":
        lines.pop()
    if lines:
        lines[0] = lines[0].removeprefix(_SIGNATURE)
    starts = [n for n, line in enumerate(lines, 1) if line.startswith(_FF)]
    if lines and not lines[0].startswith(_FF):
        starts.insert(0, 1)
    ends = [start - 1 for start in starts[1:]] + [len(lines)]
    return list(zip(starts, ends))
