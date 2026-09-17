"""Read a spreadsheet as MTSV sheets.

Functions:
read -- read the sheets of the file that a URI identifies
"""

__all__ = ["read"]

from typing import Any

import mtsv
from mtsv.integrations import FORMATS

from ai_spreadsheets import _address

# The media type registration of MTSV declares this extension, in
# draft-demosra-mtsv-00, Section 9.1.
_MTSV = ".mtsv"


def read(uri: str, /, errors: str = "strict") -> list[dict[str, Any]]:
    """Read the sheets of the file that a URI identifies.

    The file extension names the format. With errors="strict", raise
    ValueError if anything outside MTSV would be left behind. With
    errors="ignore", leave it behind.
    """
    path = _address.path(uri)
    if path.suffix == _MTSV:
        with path.open("rb") as fp:
            return mtsv.load(fp)
    if path.suffix not in FORMATS:
        raise ValueError(f"no format reads {path.suffix!r}")
    with path.open("rb") as fp:
        return FORMATS[path.suffix].load(fp, errors=errors)
