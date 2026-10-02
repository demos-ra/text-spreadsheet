"""What every reply states of its files and sheets, from big to small.

Functions:
of -- return the report of a call as MTSV sheets
"""

__all__ = ["of"]

from typing import Any

from text_spreadsheet import _field, _positions


def of(
    group: list[dict[str, Any]], selection: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Return the report of a call as MTSV sheets.

    group -- the files of the call, as the input named them
    selection -- the sheets of the call, as they were selected

    Return four sheets: file, not read, left behind and sheets.
    POSIX.1-2017 XCU 1.4, CONSEQUENCES OF ERRORS: a diagnostic message
    is written "whenever an error condition occurs".
    """
    return [
        _files(group),
        _not_read(group),
        _left_behind(group),
        _sheets(selection),
    ]


def _files(group: list[dict[str, Any]]) -> dict[str, Any]:
    """Return the sheet naming each file and its source, read or not.

    group -- the files of the call

    CSVW, 4.2 Tables: url is "the URL of the source of the data in the
    table".
    """
    return {
        "sheet name": "file",
        "header": ["file", "source"],
        "records": [
            [str(file["file"]), _field.written(str(file["source"]))] for file in group
        ],
    }


def _not_read(group: list[dict[str, Any]]) -> dict[str, Any]:
    """Return the sheet naming each file that was not read, and why.

    group -- the files of the call

    CSVW, 4.1 Table groups: notes are annotations on the group.
    """
    return {
        "sheet name": "not read",
        "header": ["file", "status"],
        "records": [
            [str(file["file"]), file["not read"]]
            for file in group
            if file["not read"] is not None
        ],
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


def _sheets(selection: list[dict[str, Any]]) -> dict[str, Any]:
    """Return the sheet naming each sheet chosen, and what came of it.

    selection -- the sheets of the call

    CSVW, 4.4 Rows: a row has a number among the rows selected and a
    source number in the original; records counts the sheet, matches
    what the condition keeps, and positions names the records the call
    names.
    """
    return {
        "sheet name": "sheets",
        "header": ["file", "sheet", "sheet name", "records", "matches", "positions"],
        "records": [
            [
                str(entry["file"]),
                str(entry["sheet"]),
                entry["part"]["sheet name"],
                str(entry["records"]),
                str(entry["matches"]),
                _positions.selection(entry["positions"]),
            ]
            for entry in selection
        ],
    }
