"""Where the MTSV copy of a source file is kept, and whether it is fresh.

Functions:
artifact -- return the path of the MTSV copy of a source file
is_fresh -- return whether a stored copy may be used instead of its source
store -- put the bytes of a copy where the copy lives
"""

__all__ = ["artifact", "is_fresh", "store"]

from pathlib import Path

from mtsv.integrations import MTSV
from platformdirs import user_cache_dir

# platformdirs, Platform details: user_cache_dir is the user's cache
# directory, with a Cache subdirectory on Windows. Parameter reference,
# appauthor: False leaves out the author directory Windows would
# otherwise add above the application's own.
_APPNAME = "text-spreadsheet"

_WORKING = ".part"


def artifact(source: Path) -> Path:
    """Return the path of the MTSV copy of a source file.

    source -- the absolute path of a file to convert

    Return the path under the cache directory. Raise ValueError for a
    path that is not absolute. RFC 9111, 2: the cache key is the
    target URI, here the source path, so the file's whole name is kept
    and the MTSV extension added to it.
    """
    if not source.is_absolute():
        raise ValueError(f"the path of a source file is absolute: {source}")
    mirrored = Path(*source.parts[1:])
    named = mirrored.with_name(mirrored.name + MTSV)
    return Path(user_cache_dir(_APPNAME, appauthor=False)) / named


def is_fresh(source: Path, stored: Path) -> bool:
    """Return whether a stored copy may be used instead of its source.

    source -- the absolute path of the file that was converted
    stored -- the path artifact returned for it

    RFC 9111, 4.2: "A 'fresh' response is one whose age has not yet
    exceeded its freshness lifetime." The validator is the modification
    time, which 4.3.1 gives as the weaker of the two.
    """
    return stored.exists() and stored.stat().st_mtime >= source.stat().st_mtime


def store(stored: Path, data: bytes) -> None:
    """Put the bytes of a copy where the copy lives.

    stored -- the path artifact returned for a source file
    data -- the MTSV bytes of the copy

    Raise OSError where the copy cannot be written. POSIX.1-2017,
    rename: "a link named new shall remain visible to other threads
    throughout the renaming operation and refer either to the file
    referred to by new or old before the operation began."
    """
    stored.parent.mkdir(parents=True, exist_ok=True)
    working = stored.with_name(stored.name + _WORKING)
    working.write_bytes(data)
    working.replace(stored)
