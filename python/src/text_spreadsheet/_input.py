"""What a pathname names: a file, or a directory of files, in order.

Functions:
of -- return the group of files a pathname names, each as converted
"""

__all__ = ["of"]

import os
from pathlib import Path
from typing import Any

from text_spreadsheet import _conversion, _field, _refusal

# POSIX.1-2017 XCU 2.13.3, rule 2: a filename beginning with a period
# is not matched by the asterisk.
_HIDDEN = "."

_NO_FORMAT = "no format"
_SKIPPED = "skipped: {}"
_DIRECTORY = "directory"
_NOT_A_REGULAR_FILE = "not a regular file"
_FAILED = "failed: {}"
_NAME_CANNOT_BE_WRITTEN = "name cannot be written"


def of(pathname: str) -> list[dict[str, Any]]:
    """Return the group of files a pathname names, each as converted.

    pathname -- the absolute pathname of a file or a directory

    Return one entry per file, or per member of a directory: its
    position from 1, its source, its status where it was not read, and
    what its conversion gives. A member that is not a regular file is
    skipped. Raise ValueRefusalError for a pathname that is not
    absolute, and OSRefusalError for a directory that cannot be listed
    or a pathname that names neither a directory nor a regular file;
    and, for a file named directly, OSRefusalError where it cannot be
    read, LookupRefusalError where its extension names no format, and
    ValueRefusalError where it cannot be converted or no field can
    hold its name.
    """
    source = Path(pathname)
    if not source.is_absolute():
        raise _refusal.ValueRefusalError(f"not an absolute pathname: {source}")
    if source.is_dir():
        return [_member(n, one) for n, one in enumerate(_members(source), 1)]
    if source.exists() and not source.is_file():
        raise _refusal.OSRefusalError(f"not a regular file: {source}")
    return [_file(1, source)]


def _members(directory: Path) -> list[Path]:
    """Return the members of a directory, from one listing, in order.

    directory -- the absolute pathname of a directory

    Return them sorted byte by byte. Raise OSRefusalError where the
    directory cannot be listed. POSIX.1-2017 XSH readdir: whether a
    file added or removed during a listing is returned is unspecified.
    XCU 2.13.3, rule 3: the pattern is replaced with the existing
    filenames it matches, sorted by the collating sequence, and
    "byte-by-byte using the collating sequence for the POSIX locale".
    """
    try:
        with os.scandir(directory) as entries:
            members = [
                Path(entry.path)
                for entry in entries
                if not entry.name.startswith(_HIDDEN)
            ]
    except OSError as error:
        raise _refusal.of(error) from error
    return sorted(members, key=lambda one: os.fsencode(one.name))


def _member(position: int, source: Path) -> dict[str, Any]:
    """Return a member's entry, naming a skip or a failure.

    position -- its position in the directory, from 1
    source -- its absolute pathname

    POSIX.1-2017 XCU 1.4, CONSEQUENCES OF ERRORS: where the action
    cannot be performed on a file in a hierarchy, processing continues
    with the remaining files.
    """
    if source.is_dir():
        return _entry(position, source, _SKIPPED.format(_DIRECTORY))
    if not source.is_file():
        return _entry(position, source, _SKIPPED.format(_NOT_A_REGULAR_FILE))
    try:
        return _file(position, source)
    except _refusal.LookupRefusalError:
        return _entry(position, source, _NO_FORMAT)
    except _refusal.RefusalError as error:
        return _entry(position, source, _FAILED.format(_field.written(str(error))))


def _file(position: int, source: Path) -> dict[str, Any]:
    """Return the entry of one file, as converted.

    position -- its position in the group, from 1
    source -- its absolute pathname

    Raise OSRefusalError, LookupRefusalError or ValueRefusalError where
    it cannot be read, and ValueRefusalError where no field can hold
    its name. The draft, Generators: a generator MUST NOT write a field
    that contains HT, LF, FF, or CR.
    """
    if not _field.holds(str(source)):
        raise _refusal.ValueRefusalError(_NAME_CANNOT_BE_WRITTEN)
    return _entry(position, source, None, _conversion.of(source))


def _entry(
    position: int,
    source: Path,
    not_read: str | None,
    converted: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return the entry of one file.

    position -- its position in the group, from 1
    source -- its absolute pathname
    not_read -- its status where it was not read: no format, skipped
        and what, or failed and the reason, as a field holds it; None
        where it was read
    converted -- what its conversion gives, or None where there is none
    """
    if converted is None:
        converted = {"left behind": [], "sheets": []}
    return {"file": position, "source": source, "not read": not_read, **converted}
