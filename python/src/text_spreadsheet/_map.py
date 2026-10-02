"""What the map answers with: the names of the fields of each sheet.

Functions:
of -- return the map of a selection as MTSV sheets
"""

__all__ = ["of"]

from typing import Any


def of(selection: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return the map of a selection as MTSV sheets.

    selection -- the sheets of the call, as they were selected

    Return one sheet, fields: each field of each header, by its
    position, with its name. The draft, Conventions and Definitions:
    the header "contains the name of each field".
    """
    records = []
    for entry in selection:
        for position, name in enumerate(entry["part"]["header"] or [], 1):
            records.append(
                [str(entry["file"]), str(entry["sheet"]), str(position), name]
            )
    return [
        {
            "sheet name": "fields",
            "header": ["file", "sheet", "field", "field name"],
            "records": records,
        }
    ]
