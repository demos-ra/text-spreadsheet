"""How one file becomes MTSV text: read in place, stored, or converted.

Functions:
of -- return the MTSV text of a file, and what its conversion left
"""

__all__ = ["of"]

from pathlib import Path
from typing import Any

import mtsv
from mtsv import integrations

from text_spreadsheet import _cache, _field, _left_behind


def of(source: Path) -> dict[str, Any]:
    """Return the MTSV text of a file, and what its conversion left.

    source -- the absolute path of a file

    Return its artifact, whether this call converted it, what the
    conversion left behind as fields hold it, its MTSV text and its
    sheets. A copy or metadata that cannot be read is made again. Raise
    OSError where the file cannot be read, LookupError where its
    extension names no format, and ValueError where it cannot be
    converted.
    """
    if source.suffix == integrations.MTSV:
        text = source.read_bytes().decode("utf-8")
        return _converted(source, False, [], text, mtsv.loads(text))
    integrations.lookup(source.suffix)
    stored = _cache.artifact(source)
    if _cache.is_fresh(source, stored):
        kept = _kept(stored)
        if kept is not None:
            return kept
    with _left_behind.collect() as reported:
        with source.open("rb") as fp:
            sheets = integrations.load(source.suffix, fp, errors="ignore")
    left_behind = [_field.written(name) for name in reported]
    text = mtsv.dumps(sheets)
    _cache.store(stored, text, left_behind)
    return _converted(stored, True, left_behind, text, sheets)


def _kept(stored: Path) -> dict[str, Any] | None:
    """Return what a kept copy gives, or None where it cannot be read.

    stored -- the path of the copy

    XDG Base Directory Specification, Basics: cached data is
    non-essential.
    """
    try:
        text, left_behind = _cache.load(stored)
        return _converted(stored, False, left_behind, text, mtsv.loads(text))
    except (OSError, ValueError):
        return None


def _converted(
    artifact: Path,
    converted: bool,
    left_behind: list[str],
    text: str,
    sheets: list[dict[str, Any]],
) -> dict[str, Any]:
    """Return what the conversion of one file gives.

    artifact -- where its MTSV text is
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
