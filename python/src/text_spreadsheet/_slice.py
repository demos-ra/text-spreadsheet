"""How an address is written, and which sheets, records and fields it names.

Functions:
of -- return the sheets an address names
"""

__all__ = ["of"]

import re
from typing import Any

# RFC 7111, 3. Fragment Identification Syntax: a selection is one spec,
# or several joined by ";", and a spec is a position or two positions
# joined by "-". Positions count from 1.
_LIST = ";"
_RANGE = "-"
_POSITION = re.compile("[0-9]+")


def of(
    sheets: list[dict[str, Any]],
    sheet: str | None = None,
    rows: str | None = None,
    fields: str | None = None,
) -> list[dict[str, Any]]:
    """Return the sheets an address names.

    sheets -- the sheets of a file
    sheet -- which sheets, or None for all of them
    rows -- which records of each, or None for all of them
    fields -- which fields of each record, or None for all of them

    Raise ValueError for an address that is not written as RFC 7111
    writes one, or that names a position the file does not have.
    """
    chosen = _chosen(sheets, sheet)
    if rows is None and fields is None:
        return chosen
    return [_cut(one, rows, fields) for one in chosen]


def _chosen(sheets: list[dict[str, Any]], sheet: str | None) -> list[dict[str, Any]]:
    """Return the sheets an address names, in the order it names them."""
    if sheet is None:
        return sheets
    return [sheets[number - 1] for number in _positions(sheet, len(sheets))]


def _cut(sheet: dict[str, Any], rows: str | None, fields: str | None) -> dict[str, Any]:
    """Return one sheet, cut to the records and fields an address names.

    The draft, Data Model: a sheet is a header and a sequence of
    records, so a cut sheet keeps its header, and a header is cut by
    the same field positions as its records.
    """
    header = sheet["header"]
    records = sheet["records"]
    if rows is not None:
        records = [records[number - 1] for number in _positions(rows, len(records))]
    if fields is not None and header is not None:
        width = len(header)
        wanted = _positions(fields, width)
        header = [header[number - 1] for number in wanted]
        records = [[record[number - 1] for number in wanted] for record in records]
    return {
        "sheet name": sheet["sheet name"],
        "header": header,
        "records": records,
    }


def _positions(address: str, count: int) -> list[int]:
    """Return the positions an address names, in the order written.

    address -- one or more specs joined by ";"
    count -- how many there are to choose from

    Raise ValueError for a spec that is not a position or a range of
    two, for a position below 1, and for one above count.
    """
    numbers = []
    for spec in address.split(_LIST):
        first, separator, last = spec.partition(_RANGE)
        if not separator:
            last = first
        if not _POSITION.fullmatch(first) or not _POSITION.fullmatch(last):
            raise ValueError(f"not an address: {address!r}")
        if int(first) < 1 or int(last) > count or int(first) > int(last):
            raise ValueError(f"the file has no {spec!r} of {count}")
        numbers.extend(range(int(first), int(last) + 1))
    return numbers
