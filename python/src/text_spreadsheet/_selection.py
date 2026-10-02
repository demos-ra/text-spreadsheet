"""Which sheets, records and fields a call names, and in what order.

Types:
Condition -- which records of a sheet to keep

Functions:
of -- return the selection a call names from a group of files
values -- return the parts a selection names, as sheets
"""

__all__ = ["Condition", "of", "values"]

from typing import Any, Callable

from text_spreadsheet import _positions

# A condition takes the records of a sheet, and returns the positions,
# from 1, of the records it keeps.
Condition = Callable[[list[list[str]]], list[int]]

_Specs = list[_positions.Spec] | None


def of(
    group: list[dict[str, Any]],
    sheet: str | None = None,
    records: str | None = None,
    fields: str | None = None,
    condition: Condition | None = None,
) -> list[dict[str, Any]]:
    """Return the selection a call names from a group of files.

    group -- the files of a call, each with its sheets
    sheet -- which sheets of each file, or None for all of them
    records -- which records of each sheet, or None for all of them
    fields -- which fields of each record, or None for all of them
    condition -- which records to keep, or None for all of them

    Return one entry per sheet named: its file, its position in that
    file, the part named, the positions in the sheet of the records
    named, and how many records the sheet has and how many the
    condition keeps. Sheets are chosen first, in each file; the
    condition sees each whole record; records counts the records it
    keeps, and fields cuts what records names; a sheet left with no
    field is empty. Raise ValueRefusalError for a selection that is not
    written as the syntax writes one, whatever there is to choose from.
    """
    sheets = _specs(sheet)
    kept = _specs(records)
    cut = _specs(fields)
    return [
        _entry(named, kept, cut, condition)
        for file in group
        for named in _named(file, sheets)
    ]


def values(selection: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return the parts a selection names, as sheets.

    selection -- what of returned
    """
    return [entry["part"] for entry in selection]


def _specs(selection: str | None) -> _Specs:
    """Return the specs a selection is written as, or None for none.

    selection -- a selection, or None

    Raise ValueRefusalError for a selection that is not written as the
    syntax writes one.
    """
    return None if selection is None else _positions.specs(selection)


def _named(file: dict[str, Any], sheets: _Specs) -> list[dict[str, Any]]:
    """Return the sheets of one file a call names, each with its place.

    file -- one file of the group, with its sheets
    sheets -- the specs of the sheets named, or None for all of them

    The draft, Data Model: "The order of the sheets is the order in
    which they appear in the file."
    """
    held = file["sheets"]
    positions = list(range(1, len(held) + 1))
    if sheets is not None:
        positions = _positions.of(sheets, len(held))
    return [{"file": file["file"], "sheet": n, "part": held[n - 1]} for n in positions]


def _entry(
    named: dict[str, Any],
    records: _Specs,
    fields: _Specs,
    condition: Condition | None,
) -> dict[str, Any]:
    """Return the entry of one sheet, cut to what the call names.

    named -- the sheet, with its file and its position in that file
    records -- the specs of the records named, or None for all of them
    fields -- the specs of the fields named, or None for all of them
    condition -- which records to keep, or None for all of them

    CSVW, 4.4 Rows: a row has a number, its position among the rows of
    the table, and a source number, its position in the original.
    """
    sheet = named["part"]
    header = sheet["header"]
    held = sheet["records"]
    kept = condition(held) if condition else list(range(1, len(held) + 1))
    chosen = kept
    if records is not None:
        chosen = [kept[n - 1] for n in _positions.of(records, len(kept))]
    part = [held[n - 1] for n in chosen]
    if fields is not None:
        wanted = _positions.of(fields, len(header or []))
        header, part = _cut(header, part, wanted)
    return {
        "file": named["file"],
        "sheet": named["sheet"],
        "part": {
            "sheet name": sheet["sheet name"],
            "header": header,
            "records": part,
        },
        "positions": chosen,
        "records": len(held),
        "matches": len(kept),
    }


def _cut(
    header: list[str] | None, records: list[list[str]], wanted: list[int]
) -> tuple[list[str] | None, list[list[str]]]:
    """Return a header and its records, cut to the fields named.

    header -- the header, or None for an empty sheet
    records -- the records named
    wanted -- the positions of the fields named, from 1

    The draft, Data Model: "A sheet with no lines is an empty sheet; it
    has neither a header nor records." Grammar: record = field *(HTAB
    field) eol.
    """
    if not wanted:
        return None, []
    return (
        [header[n - 1] for n in wanted],
        [[record[n - 1] for n in wanted] for record in records],
    )
