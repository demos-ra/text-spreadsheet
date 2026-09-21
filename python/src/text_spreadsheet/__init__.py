"""Read a spreadsheet as MTSV sheets.

Functions:
read -- read the sheets of the file that a URI identifies
"""

__all__ = ["read"]

from typing import Any

from mtsv import integrations

from text_spreadsheet import _address


def read(uri: str, /, errors: str = "strict") -> list[dict[str, Any]]:
    """Read the sheets of the file that a URI identifies.

    The file extension names the format, and the conversion is the one
    in mtsv.integrations. With errors="strict", raise ValueError if
    anything outside MTSV would be left behind. With errors="ignore",
    leave it behind.
    """
    path = _address.path(uri)
    with path.open("rb") as fp:
        return integrations.load(path.suffix, fp, errors=errors)
