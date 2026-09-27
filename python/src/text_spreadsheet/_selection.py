"""Which sheets, records and fields a call names, and in what order.

Functions:
of -- return the selection a call names from a group of files
values -- return the parts a selection names, as sheets
"""

__all__ = ["of", "values"]

from typing import Any, Callable

from text_spreadsheet import _positions

# A condition takes the records of a sheet, and returns the positions,
# from 1, of the records it keeps.
Condition = Callable[[list[list[str]]], list[int]]


def of(
    group: list[dict[str, Any]],
    sheet: str | None = None,
    rows: str | None = None,
    fields: str | None = None,
    condition: Condition | None = None,
) -> list[dict[str, Any]]:
    """Return the selection a call names from a group of files.

    group -- the files of a call, each with its sheets
    sheet -- which sheets of the group, or None for all of them
    rows -- which records of each, or None for all of them
    fields -- which fields of each record, or None for all of them
    condition -- which records to keep, or None for all of them

    Return one entry per sheet named: its position in the group, its
    file, its position in that file, the part named, and how many
    records it has and how many the condition keeps. Sheets are chosen
    first; the condition sees each whole record; rows counts the records
    it keeps, and fields cuts what rows names. Raise ValueError for an
    address that is not written as the syntax writes one.
    """
    numbered = _numbered(group)
    if sheet is not None:
        numbered = [numbered[n - 1] for n in _positions.of(sheet, len(numbered))]
    return [_entry(one, rows, fields, condition) for one in numbered]


def values(selection: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return the parts a selection names, as sheets.

    selection -- what of returned
    """
    return [entry["part"] for entry in selection]


def _numbered(group: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return every sheet of the group, numbered across its files.

    group -- the files of a call, each with its sheets
    """
    numbered = []
    for file in group:
        for position, sheet in enumerate(file["sheets"], 1):
            numbered.append(
                {
                    "sheet": len(numbered) + 1,
                    "file": file["file"],
                    "position in file": position,
                    "part": sheet,
                }
            )
    return numbered


def _entry(
    numbered: dict[str, Any],
    rows: str | None,
    fields: str | None,
    condition: Condition | None,
) -> dict[str, Any]:
    """Return the entry of one sheet, cut to what the call names.

    numbered -- the sheet, numbered in the group and in its file
    rows -- which records, or None for all of them
    fields -- which fields, or None for all of them
    condition -- which records to keep, or None for all of them

    CSVW, 4.4 Rows: a row has a number, its position among the rows of
    the table, and a source number, its position in the original.
    """
    sheet = numbered["part"]
    header = sheet["header"]
    records = sheet["records"]
    kept = condition(records) if condition else list(range(1, len(records) + 1))
    named = kept
    if rows is not None:
        named = [kept[n - 1] for n in _positions.of(rows, len(kept))]
    part = [records[n - 1] for n in named]
    if fields is not None:
        wanted = _positions.of(fields, len(header or []))
        header = None if header is None else [header[n - 1] for n in wanted]
        part = [[record[n - 1] for n in wanted] for record in part]
    return {
        "sheet": numbered["sheet"],
        "file": numbered["file"],
        "position in file": numbered["position in file"],
        "part": {
            "sheet name": sheet["sheet name"],
            "header": header,
            "records": part,
        },
        "records": len(records),
        "matches": len(kept),
    }
