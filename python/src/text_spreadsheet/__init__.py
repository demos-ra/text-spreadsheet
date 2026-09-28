"""Read spreadsheets as Multi-Sheet Tab-Separated Values (MTSV) text.

The draft is draft-demosra-mtsv-01; the modules cite it by section.

Functions:
read -- return the map of a file or folder, or the part an address names
"""

__all__ = ["read"]

from functools import partial

import mtsv

from text_spreadsheet import _filter, _input, _map, _selection


def read(
    path: str,
    /,
    sheet: str | None = None,
    rows: str | None = None,
    fields: str | None = None,
    filter: str | None = None,
) -> str:
    """Return the map of a file or folder, or the part an address names.

    path -- the absolute path of a file, or of a folder of files
    sheet -- which sheets, or None for all of them
    rows -- which records of each sheet
    fields -- which fields of each record
    filter -- which records to keep, an RFC 9535 logical-expr

    With no position, return the map of what the filter keeps; with a
    position, return that part. Raise ValueError for a path that is not
    absolute, an address or filter that is not written as its syntax
    writes one, or a file named directly that cannot be converted;
    LookupError for a file named directly whose extension names no
    format; and OSError for a folder that cannot be listed, or a file
    named directly that cannot be read.
    """
    condition = None
    if filter is not None:
        condition = partial(_filter.matches, _filter.compile(filter))
    group = _input.of(path)
    selection = _selection.of(group, sheet, rows, fields, condition)
    if sheet is None and rows is None and fields is None:
        return mtsv.dumps(_map.of(group, selection))
    return mtsv.dumps(_selection.values(selection))
