"""Read a spreadsheet as MTSV text.

Functions:
read -- return the map of a file, or the part of it an address names
"""

__all__ = ["read"]

import io
from pathlib import Path
from typing import Any

import mtsv
from mtsv import integrations

from text_spreadsheet import _cache, _map, _report, _slice


def read(
    path: str,
    /,
    sheet: str | None = None,
    rows: str | None = None,
    fields: str | None = None,
) -> str:
    """Return the map of a file, or the part of it an address names.

    path -- the absolute path of the file to read
    sheet -- which sheets, or None for the map of the file
    rows -- which records of each sheet
    fields -- which fields of each record

    Convert the file and keep the copy, or read the copy when the file
    is no newer than it. Raise ValueError for a path that is not
    absolute, a file that cannot be converted, or an address the file
    cannot answer; LookupError for an extension that names no format;
    and OSError for a file that cannot be read, or a copy that cannot
    be written.
    """
    source = Path(path)
    stored = _cache.artifact(source)
    converted = not _cache.is_fresh(source, stored)
    left_behind: list[str] = []
    if converted:
        with _report.collect() as left_behind:
            sheets = _converted(source, stored)
    else:
        sheets = _stored(stored)
    if sheet is None and rows is None and fields is None:
        return mtsv.dumps(_map.of(sheets, source, stored, converted, left_behind))
    return mtsv.dumps(_slice.of(sheets, sheet, rows, fields))


def _converted(source: Path, stored: Path) -> list[dict[str, Any]]:
    """Convert a file, keep the copy, and return its sheets."""
    with source.open("rb") as fp:
        sheets = integrations.load(source.suffix, fp, errors="ignore")
    with io.BytesIO() as out:
        mtsv.dump(sheets, out)
        _cache.store(stored, out.getvalue())
    return sheets


def _stored(stored: Path) -> list[dict[str, Any]]:
    """Return the sheets of a copy that may still be used."""
    with stored.open("rb") as fp:
        return mtsv.load(fp)
