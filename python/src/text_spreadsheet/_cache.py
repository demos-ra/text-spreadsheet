"""Where the MTSV copy of a source file is kept, and when it is fresh.

Functions:
artifact -- return the path of the MTSV copy of a source file
is_fresh -- return whether a copy may be used instead of its source
store -- keep a copy, and what its conversion left behind
load -- return a copy, and what its conversion left behind
"""

__all__ = ["artifact", "is_fresh", "store", "load"]

import io
import os
from pathlib import Path

import mtsv
from mtsv.integrations import MTSV
from platformdirs import user_cache_dir

# platformdirs, Platform details: user_cache_dir is the user's cache
# directory, with a Cache subdirectory on Windows. Parameter reference,
# appauthor: False leaves out the author directory Windows would
# otherwise add above the application's own.
_APPNAME = "text-spreadsheet"

# CSVW, 5.3 Default Locations and Site-wide Location Configuration: the
# default location of metadata is {+url}-metadata.json.
_METADATA = "-metadata" + MTSV
_LEFT_BEHIND = "left behind"
_WHAT = "what"

# POSIX.1-2017 XCU 1.4, OUTPUT FILES: temporary files are named so that
# multiple instances can operate simultaneously, by process ID.
_WORKING = ".{pid}.part"


def artifact(source: Path) -> Path:
    """Return the path of the MTSV copy of a source file.

    source -- the absolute path of a file to convert

    Return the path under the cache directory, the source path with the
    MTSV extension added to its whole name. Raise ValueError for a path
    that is not absolute. RFC 9111, 2: the cache key is the target URI,
    here the source path.
    """
    if not source.is_absolute():
        raise ValueError(f"the path of a source file is absolute: {source}")
    mirrored = Path(*source.parts[1:])
    named = mirrored.with_name(mirrored.name + MTSV)
    return Path(user_cache_dir(_APPNAME, appauthor=False)) / named


def is_fresh(source: Path, stored: Path) -> bool:
    """Return whether a copy may be used instead of its source.

    source -- the absolute path of the file that was converted
    stored -- the path artifact returned for it

    RFC 9111, 4.2: "A 'fresh' response is one whose age has not yet
    exceeded its freshness lifetime." The validator is the modification
    time, which 4.3.1 gives as the weaker of the two. A copy is fresh
    only with its metadata beside it.
    """
    return (
        stored.exists()
        and _metadata(stored).exists()
        and stored.stat().st_mtime >= source.stat().st_mtime
    )


def store(stored: Path, text: str, left_behind: list[str]) -> None:
    """Keep a copy, and what its conversion left behind, beside it.

    stored -- the path artifact returned for a source file
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

    stored -- the path artifact returned for a source file

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
    """Return the path of what is known about a copy, beside it.

    stored -- the path artifact returned for a source file
    """
    return stored.with_name(stored.name + _METADATA)


def _write(path: Path, data: bytes) -> None:
    """Put bytes where a copy, or its metadata, lives.

    path -- where the bytes live
    data -- the bytes

    Raise OSError where the bytes cannot be written, leaving no working
    file behind. POSIX.1-2017, rename: "a link named new shall remain
    visible to other threads throughout the renaming operation and
    refer either to the file referred to by new or old before the
    operation began." XCU 1.4, OUTPUT FILES: a temporary file is removed
    on exit because of errors.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    working = path.with_name(path.name + _WORKING.format(pid=os.getpid()))
    try:
        working.write_bytes(data)
        working.replace(path)
    except OSError:
        working.unlink(missing_ok=True)
        raise
