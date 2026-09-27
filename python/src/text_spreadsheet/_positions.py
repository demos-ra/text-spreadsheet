"""How a list of positions is written, and which positions it names.

Functions:
of -- return the positions an address names, of so many
"""

__all__ = ["of"]

import re

# RFC 7111, 3. Fragment Identification Syntax:
# singlespec = position [ "-" position ]; position = number / "*";
# number = 1*( DIGIT ); specs are joined by ";".
_LIST = ";"
_RANGE = "-"
_LAST = "*"
_NUMBER = re.compile("[0-9]+")


def of(address: str, count: int) -> list[int]:
    """Return the positions an address names, of so many.

    address -- one spec, or several joined by ";"
    count -- how many there are to choose from

    Return the positions in the order the specs are written, a position
    named twice given twice. Raise ValueError for an address that is not
    written as the syntax writes one.
    """
    positions = []
    for spec in address.split(_LIST):
        positions.extend(_spec(spec, address, count))
    return positions


def _spec(spec: str, address: str, count: int) -> list[int]:
    """Return the positions one spec names.

    spec -- one position, or two joined by "-"
    address -- the whole address, named in an error
    count -- how many there are to choose from

    RFC 7111, 4.2. Semantics of Fragment Identifiers: a single selection
    of a non-existing row is ignored; a range extends only to the actual
    size; a range that selects inversely is ignored; each specification
    is processed independently.
    """
    first, separator, last = spec.partition(_RANGE)
    start = _position(first, address, count)
    if not separator:
        return [start] if 1 <= start <= count else []
    end = _position(last, address, count)
    if start > end:
        return []
    return list(range(max(start, 1), min(end, count) + 1))


def _position(text: str, address: str, count: int) -> int:
    """Return one position: a number, or "*" for the last.

    text -- the position as written
    address -- the whole address, named in an error
    count -- how many there are to choose from

    Raise ValueError for text that is neither. RFC 7111, 4.2. Semantics
    of Fragment Identifiers: rows are counted from one, and "*" refers
    to the last row or column.
    """
    if text == _LAST:
        return count
    if not _NUMBER.fullmatch(text):
        raise ValueError(f"not an address: {address!r}")
    return int(text)
