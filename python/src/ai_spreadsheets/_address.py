"""Turn a file URI into the local path it identifies.

Functions:
path -- return the local path that a file URI identifies
"""

__all__ = ["path"]

from pathlib import Path
from urllib.parse import unquote, urlsplit

# RFC 8089, Section 2: file-URI = "file" ":" file-hier-part, where
# file-hier-part is "//" auth-path or a local-path, and local-path is
# the path-absolute rule of RFC 3986. A file URI carries neither a
# query nor a fragment.
_SCHEME = "file"

# RFC 8089, Section 3: a file URI can be translated to a local path
# only if it is local, which it is when it has no authority or the
# authority is the special string "localhost".
_LOCAL = ("", "localhost")


def path(uri: str, /) -> Path:
    """Return the local path that a file URI identifies.

    Raise ValueError for anything that is not a local file URI.
    Section 3.1 of RFC 3986 asks that a URI breaking a rule of its own
    scheme be flagged as an error rather than read for its parts.
    """
    parts = urlsplit(uri)
    # RFC 3986, Section 3.1: schemes are case-insensitive.
    if parts.scheme.lower() != _SCHEME:
        raise ValueError(f"not a file URI: {uri!r}")
    if parts.netloc.lower() not in _LOCAL:
        raise ValueError(f"the file URI is not local: {uri!r}")
    if parts.query or parts.fragment:
        raise ValueError(f"a file URI has no query or fragment: {uri!r}")
    # RFC 8089, Section 4: the path is UTF-8, then percent-encoded.
    decoded = unquote(parts.path, encoding="utf-8", errors="strict")
    if not decoded.startswith("/"):
        raise ValueError(f"the path of a file URI is absolute: {uri!r}")
    return Path(decoded)
