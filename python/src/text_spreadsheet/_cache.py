"""Where the MTSV copy of a source file is kept, and whether it is fresh.

Functions:
artifact -- return the path of the MTSV copy of a source file
is_fresh -- return whether a stored copy may be used instead of its source
"""

__all__ = ["artifact", "is_fresh"]

from pathlib import Path

from mtsv.integrations import MTSV
from platformdirs import user_cache_dir

# platformdirs, Platform details: user_cache_dir is the user's cache
# directory, with a Cache subdirectory on Windows. Parameter reference,
# appauthor: False leaves out the author directory Windows would
# otherwise add above the application's own.
_APPNAME = "text-spreadsheet"


def artifact(source: Path) -> Path:
    """Return the path of the MTSV copy of a source file.

    source -- the absolute path of a file to convert

    Return the path under the cache directory. Raise ValueError for a
    path that is not absolute.
    """
    if not source.is_absolute():
        raise ValueError(f"the path of a source file is absolute: {source}")
    mirrored = Path(*source.parts[1:]).with_suffix(MTSV)
    return Path(user_cache_dir(_APPNAME, appauthor=False)) / mirrored


def is_fresh(source: Path, stored: Path) -> bool:
    """Return whether a stored copy may be used instead of its source.

    source -- the absolute path of the file that was converted
    stored -- the path artifact returned for it

    RFC 9111, 4.2: "A 'fresh' response is one whose age has not yet
    exceeded its freshness lifetime." The validator is the modification
    time, which 4.3.1 gives as the weaker of the two.
    """
    return stored.exists() and stored.stat().st_mtime >= source.stat().st_mtime
