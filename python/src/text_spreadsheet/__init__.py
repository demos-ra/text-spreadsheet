"""Read spreadsheets as Multi-Sheet Tab-Separated Values (MTSV) text.

The draft is draft-demosra-mtsv-01; the modules cite it by section.

Functions:
read -- return the report of a file or directory, then its map, or
    the values a selection names
"""

__all__ = ["read"]

from functools import partial

import mtsv

from text_spreadsheet import _filter, _input, _map, _report, _selection


def read(
    pathname: str,
    /,
    sheet: str | None = None,
    records: str | None = None,
    fields: str | None = None,
    filter: str | None = None,
) -> str:
    """Return the report of a call, then its map, or the values.

    pathname -- the absolute pathname of a file, or of a directory
    sheet -- which sheets of each file, or None for all of them
    records -- which records of each sheet
    fields -- which fields of each record
    filter -- which records to keep, an RFC 9535 logical-expr

    Return the report first: the files, what was not read, what was
    left behind, and the sheets chosen with what the filter keeps.
    Then, with no selection, the map, the names of their fields; with
    one, those values.

    Raise ValueError for a pathname that is not absolute, a selection
    or filter that is not written as its syntax writes one, or a file
    named directly that cannot be converted or whose name no field can
    hold; LookupError for a file named directly whose extension names
    no format; and OSError for a directory that cannot be listed, a
    pathname that names neither a directory nor a regular file, or a
    file named directly that cannot be read.
    """
    condition = None
    if filter is not None:
        condition = partial(_filter.matches, _filter.compile(filter))
    group = _input.of(pathname)
    selection = _selection.of(group, sheet, records, fields, condition)
    if sheet is None and records is None and fields is None:
        answer = _map.of(selection)
    else:
        answer = _selection.values(selection)
    return mtsv.dumps(_report.of(group, selection) + answer)
