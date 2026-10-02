"""How one file becomes MTSV sheets: read in place, kept, or converted.

Functions:
of -- return the sheets of a file, and what its conversion left
"""

__all__ = ["of"]

from pathlib import Path
from typing import Any

import mtsv
from mtsv import integrations

from text_spreadsheet import _cache, _field, _left_behind, _refusal


def of(source: Path) -> dict[str, Any]:
    """Return the sheets of a file, and what its conversion left.

    source -- the absolute pathname of a file

    Return what the conversion left behind, as fields hold it, and the
    file's sheets. A copy or metadata that cannot be read is made
    again, and a copy that cannot be written is not kept. Raise
    OSRefusalError where the file cannot be read, LookupRefusalError
    where its extension names no format, and ValueRefusalError where it
    cannot be converted, or where its pathname can name no file.
    """
    if source.suffix == integrations.MTSV:
        return _converted([], _in_place(source))
    try:
        integrations.lookup(source.suffix)
        modified = source.stat().st_mtime
    except (LookupError, OSError, ValueError) as error:
        raise _refusal.of(error) from error
    stored = _cache.location(source)
    if _cache.is_fresh(stored, modified):
        kept = _kept(stored)
        if kept is not None:
            return kept
    with _left_behind.collect() as reported:
        sheets = _loaded(source)
    left_behind = [_field.written(name) for name in reported]
    _keep(stored, mtsv.dumps(sheets), left_behind)
    return _converted(left_behind, sheets)


def _in_place(source: Path) -> list[dict[str, Any]]:
    """Return the sheets of an MTSV file, read where it is.

    source -- the absolute pathname of an MTSV file

    Raise OSRefusalError where it cannot be read, and ValueRefusalError
    where it is not MTSV.
    """
    try:
        return mtsv.loads(source.read_bytes().decode("utf-8"))
    except (OSError, ValueError) as error:
        raise _refusal.of(error) from error


def _kept(stored: Path) -> dict[str, Any] | None:
    """Return what a kept copy gives, or None where it cannot be read.

    stored -- the pathname of the copy

    XDG Base Directory Specification, Basics: cached data is
    non-essential.
    """
    try:
        text, left_behind = _cache.load(stored)
        sheets = mtsv.loads(text)
    except (OSError, ValueError):
        return None
    return _converted(left_behind, sheets)


def _loaded(source: Path) -> list[dict[str, Any]]:
    """Return the sheets of a file, as mtsv loads them.

    source -- the absolute pathname of a file whose extension names a
        format

    Raise OSRefusalError where it cannot be read, and ValueRefusalError
    where mtsv refuses it. mtsv, What is left behind: text that MTSV
    cannot hold, such as a tab or line break inside a value, always
    raises ValueError.
    """
    try:
        with source.open("rb") as fp:
            return integrations.load(source.suffix, fp, errors="ignore")
    except (OSError, ValueError) as error:
        raise _refusal.of(error) from error


def _keep(stored: Path, text: str, left_behind: list[str]) -> None:
    """Keep a copy where it can be written.

    stored -- the pathname location returned for the file
    text -- its MTSV text
    left_behind -- what its conversion left behind, as fields hold it

    A copy that cannot be written is not kept. XDG Base Directory
    Specification, Basics: cached data is non-essential.
    """
    try:
        _cache.store(stored, text, left_behind)
    except OSError:
        pass


def _converted(left_behind: list[str], sheets: list[dict[str, Any]]) -> dict[str, Any]:
    """Return what the conversion of one file gives.

    left_behind -- what the conversion left behind, as fields hold it
    sheets -- its sheets
    """
    return {"left behind": left_behind, "sheets": sheets}
