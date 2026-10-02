"""Where the MTSV copy of a source file is kept, and when it is fresh.

Functions:
location -- return where the MTSV copy of a source file is kept
is_fresh -- return whether a copy may be used instead of its source
store -- keep a copy, and what its conversion left behind
load -- return a copy, and what its conversion left behind
"""

__all__ = ["location", "is_fresh", "store", "load"]

import io
import os
import threading
from pathlib import Path

import mtsv
from mtsv.integrations import MTSV
from platformdirs import user_cache_dir

# platformdirs, Platform details: user_cache_dir is the user's cache
# directory. Parameter reference, appname: used as a subdirectory.
_APPNAME = "text-spreadsheet"

# CSVW, 5.3 Default Locations and Site-wide Location Configuration: the
# default location of metadata is {+url}-metadata.json.
_METADATA = "-metadata" + MTSV
_LEFT_BEHIND = "left behind"
_WHAT = "what"

# POSIX.1-2017 XCU 1.4, OUTPUT FILES: temporary files are named so that
# multiple instances can operate simultaneously, by process ID. MCP
# Python SDK, Tools: a plain function runs in a thread.
_WORKING = ".{pid}.{thread}.part"


def location(source: Path) -> Path:
    """Return where the MTSV copy of a source file is kept.

    source -- the absolute pathname of a file to convert

    Return the pathname under the cache directory: the file's resolved
    pathname, mirrored, with the MTSV extension added to its whole
    name. POSIX.1-2017 XSH realpath: "an absolute pathname that
    resolves to the same directory entry, whose resolution does not
    involve '.', '..', or symbolic links". RFC 9111, 2: the cache key
    is the target URI, here that pathname.
    """
    resolved = Path(os.path.realpath(source))
    mirrored = Path(*resolved.parts[1:])
    named = mirrored.with_name(mirrored.name + MTSV)
    return Path(user_cache_dir(_APPNAME)) / named


def is_fresh(stored: Path, modified: float) -> bool:
    """Return whether a copy may be used instead of its source.

    stored -- the pathname location returned for a source file
    modified -- the modification time of the source file

    RFC 9111, 4.2: "A 'fresh' response is one whose age has not yet
    exceeded its freshness lifetime." The validator is the modification
    time, which 4.3.1 gives as the weaker of the two. A copy is fresh
    only with its metadata beside it, and a copy that cannot be
    examined is not fresh. XDG Base Directory Specification, Basics:
    cached data is non-essential.
    """
    try:
        return (
            stored.exists()
            and _metadata(stored).exists()
            and stored.stat().st_mtime >= modified
        )
    except OSError:
        return False


def store(stored: Path, text: str, left_behind: list[str]) -> None:
    """Keep a copy, and what its conversion left behind, beside it.

    stored -- the pathname location returned for a source file
    text -- the MTSV text of the copy
    left_behind -- what the conversion left behind, as fields hold it

    The metadata is written first and the copy last. Raise OSError
    where either cannot be written.
    """
    sheet = {
        "sheet name": _LEFT_BEHIND,
        "header": [_WHAT],
        "records": [[name] for name in left_behind],
    }
    with io.BytesIO() as out:
        mtsv.dump([sheet], out)
        _write(_metadata(stored), out.getvalue())
    _write(stored, text.encode("utf-8"))


def load(stored: Path) -> tuple[str, list[str]]:
    """Return a copy, and what its conversion left behind.

    stored -- the pathname location returned for a source file

    Return the MTSV text of the copy and the names from its metadata.
    Raise OSError where either cannot be read, and ValueError where
    either is not as store writes it.
    """
    with _metadata(stored).open("rb") as fp:
        sheets = mtsv.load(fp)
    layout = [(sheet["sheet name"], sheet["header"]) for sheet in sheets]
    if layout != [(_LEFT_BEHIND, [_WHAT])]:
        raise ValueError(f"not the metadata of a copy: {_metadata(stored)}")
    names = [record[0] for record in sheets[0]["records"]]
    return stored.read_bytes().decode("utf-8"), names


def _metadata(stored: Path) -> Path:
    """Return the pathname of what is known about a copy, beside it.

    stored -- the pathname location returned for a source file
    """
    return stored.with_name(stored.name + _METADATA)


def _write(pathname: Path, data: bytes) -> None:
    """Put bytes where a copy, or its metadata, is kept.

    pathname -- where the bytes are kept
    data -- the bytes

    Raise OSError where the bytes cannot be written, leaving no working
    file behind. POSIX.1-2017, rename: "a link named new shall remain
    visible to other threads throughout the renaming operation and
    refer either to the file referred to by new or old before the
    operation began." XCU 1.4, OUTPUT FILES: a temporary file is removed
    on exit because of errors.
    """
    _made(pathname.parent)
    working = pathname.with_name(
        pathname.name + _WORKING.format(pid=os.getpid(), thread=threading.get_ident())
    )
    try:
        working.write_bytes(data)
        working.replace(pathname)
    except OSError:
        working.unlink(missing_ok=True)
        raise


def _made(directory: Path) -> None:
    """Make a directory, and each one above it that is missing.

    directory -- the directory a copy is kept in

    Raise OSError where one cannot be made. XDG Base Directory
    Specification, Referencing this specification: "If, when attempting
    to write a file, the destination directory is non-existent an
    attempt should be made to create it with permission 0700. If the
    destination directory exists already the permissions should not be
    changed."
    """
    for one in reversed([directory, *directory.parents]):
        one.mkdir(mode=0o700, exist_ok=True)
