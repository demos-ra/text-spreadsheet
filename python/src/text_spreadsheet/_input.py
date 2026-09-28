"""What a path names: a file, or a folder of files, in order.

Functions:
of -- return the group of files a path names, each as converted
"""

__all__ = ["of"]

import os
from pathlib import Path
from typing import Any

from text_spreadsheet import _conversion, _field, _refusal

# POSIX.1-2017 XCU 2.13.3, rule 2: a filename beginning with a period
# is not matched by the asterisk.
_HIDDEN = "."

_READ = "read"
_NO_FORMAT = "no format"
_FAILED = "failed: {}"
_NAME_CANNOT_BE_WRITTEN = "name cannot be written"


def of(path: str) -> list[dict[str, Any]]:
    """Return the group of files a path names, each as converted.

    path -- the absolute path of a file or a folder

    Return one entry per file: its position from 1, its source, its
    status, and what its conversion gives. Raise ValueRefusalError for a
    path that is not absolute, and OSRefusalError for a folder that
    cannot be listed; and, for a file named directly, OSRefusalError
    where it cannot be read, LookupRefusalError where its extension
    names no format, and ValueRefusalError where it cannot be converted.
    """
    source = Path(path)
    if not source.is_absolute():
        raise _refusal.ValueRefusalError(
            f"the path of a source file is absolute: {source}"
        )
    if source.is_dir():
        return [_member(n, one) for n, one in enumerate(_members(source), 1)]
    return [_file(1, source)]


def _members(folder: Path) -> list[Path]:
    """Return the files a folder holds, from one listing, in order.

    folder -- the absolute path of a folder

    POSIX.1-2017 XSH readdir: whether a file added or removed during a
    listing is returned is unspecified. XCU 2.13.3, rule 3: names are
    sorted by the collating sequence, in the POSIX locale byte by byte.
    Raise OSRefusalError where the folder cannot be listed.
    """
    try:
        with os.scandir(folder) as entries:
            files = [
                Path(entry.path)
                for entry in entries
                if not entry.name.startswith(_HIDDEN) and entry.is_file()
            ]
    except OSError as error:
        raise _refusal.of(error) from error
    return sorted(files, key=lambda one: os.fsencode(one.name))


def _member(position: int, source: Path) -> dict[str, Any]:
    """Return the entry of a file in a folder, naming a failure.

    position -- its position in the folder, from 1
    source -- its absolute path

    POSIX.1-2017 XCU 1.4, CONSEQUENCES OF ERRORS: where the action
    cannot be performed on a file in a hierarchy, processing continues
    with the remaining files.
    """
    try:
        return _file(position, source)
    except _refusal.LookupRefusalError:
        return _entry(position, source, _NO_FORMAT)
    except _refusal.RefusalError as error:
        return _entry(position, source, _FAILED.format(_field.written(str(error))))


def _file(position: int, source: Path) -> dict[str, Any]:
    """Return the entry of one file, as converted.

    position -- its position in the group, from 1
    source -- its absolute path

    Raise OSRefusalError, LookupRefusalError or ValueRefusalError where
    it cannot be read.
    """
    if not _field.holds(str(source)):
        return _entry(position, source, _FAILED.format(_NAME_CANNOT_BE_WRITTEN))
    return _entry(position, source, _READ, _conversion.of(source))


def _entry(
    position: int,
    source: Path,
    status: str,
    converted: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return the entry of one file.

    position -- its position in the group, from 1
    source -- its absolute path
    status -- read, no format, or failed and the reason, as a field
        holds it
    converted -- what its conversion gives, or None where there is none
    """
    if converted is None:
        converted = {
            "artifact": None,
            "converted": False,
            "left behind": [],
            "text": "",
            "sheets": [],
        }
    return {"file": position, "source": source, "status": status, **converted}
