"""How one file becomes MTSV text: read in place, stored, or converted.

Functions:
of -- return the MTSV text of a file, and what its conversion left
"""

__all__ = ["of"]

from pathlib import Path
from typing import Any

import mtsv
from mtsv import integrations

from text_spreadsheet import _cache, _field, _left_behind, _refusal


def of(source: Path) -> dict[str, Any]:
    """Return the MTSV text of a file, and what its conversion left.

    source -- the absolute path of a file

    Return its artifact, whether this call converted it, what the
    conversion left behind as fields hold it, its MTSV text and its
    sheets. A copy or metadata that cannot be read is made again, and a
    copy that cannot be written leaves no artifact. Raise OSRefusalError
    where the file cannot be read, LookupRefusalError where its
    extension names no format, and ValueRefusalError where it cannot be
    converted.
    """
    if source.suffix == integrations.MTSV:
        text, sheets = _in_place(source)
        return _converted(source, False, [], text, sheets)
    try:
        integrations.lookup(source.suffix)
        modified = source.stat().st_mtime
    except (LookupError, OSError) as error:
        raise _refusal.of(error) from error
    stored = _cache.artifact(source)
    if _cache.is_fresh(stored, modified):
        kept = _kept(stored)
        if kept is not None:
            return kept
    with _left_behind.collect() as reported:
        sheets = _loaded(source)
    left_behind = [_field.written(name) for name in reported]
    text = mtsv.dumps(sheets)
    artifact = _stored(stored, text, left_behind)
    return _converted(artifact, True, left_behind, text, sheets)


def _in_place(source: Path) -> tuple[str, list[dict[str, Any]]]:
    """Return the text and sheets of an MTSV file, read where it is.

    source -- the absolute path of an MTSV file

    Raise OSRefusalError where it cannot be read, and ValueRefusalError
    where it is not MTSV.
    """
    try:
        text = source.read_bytes().decode("utf-8")
        sheets = mtsv.loads(text)
    except (OSError, ValueError) as error:
        raise _refusal.of(error) from error
    return text, sheets


def _kept(stored: Path) -> dict[str, Any] | None:
    """Return what a kept copy gives, or None where it cannot be read.

    stored -- the path of the copy

    XDG Base Directory Specification, Basics: cached data is
    non-essential.
    """
    try:
        text, left_behind = _cache.load(stored)
        sheets = mtsv.loads(text)
    except (OSError, ValueError):
        return None
    return _converted(stored, False, left_behind, text, sheets)


def _loaded(source: Path) -> list[dict[str, Any]]:
    """Return the sheets of a file, as mtsv loads them.

    source -- the absolute path of a file whose extension names a
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


def _stored(stored: Path, text: str, left_behind: list[str]) -> Path | None:
    """Keep a copy where it can be written, and return where it is.

    stored -- the path artifact returned for the file
    text -- its MTSV text
    left_behind -- what its conversion left behind, as fields hold it

    Return the path of the copy, or None where it cannot be written.
    XDG Base Directory Specification, Basics: cached data is
    non-essential.
    """
    try:
        _cache.store(stored, text, left_behind)
    except OSError:
        return None
    return stored


def _converted(
    artifact: Path | None,
    converted: bool,
    left_behind: list[str],
    text: str,
    sheets: list[dict[str, Any]],
) -> dict[str, Any]:
    """Return what the conversion of one file gives.

    artifact -- where its MTSV text is, or None where no copy was
        written
    converted -- whether this call converted it
    left_behind -- what the conversion left behind, as fields hold it
    text -- its MTSV text
    sheets -- its sheets
    """
    return {
        "artifact": artifact,
        "converted": converted,
        "left behind": left_behind,
        "text": text,
        "sheets": sheets,
    }
