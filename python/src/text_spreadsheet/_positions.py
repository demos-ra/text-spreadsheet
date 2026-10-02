"""How a selection is written, and which positions it names.

Types:
Spec -- one spec of a selection: its first and last position

Functions:
specs -- return the specs a selection is written as, or refuse it
of -- return the positions specs name, of so many
selection -- return the selection that names positions
"""

__all__ = ["Spec", "specs", "of", "selection"]

import re

from text_spreadsheet import _refusal

# RFC 7111, 3. Fragment Identification Syntax:
# singlespec = position [ "-" position ]; position = number / "*";
# number = 1*( DIGIT ); specs are joined by ";".
_LIST = ";"
_RANGE = "-"
_LAST = "*"
_NUMBER = re.compile("[0-9]+")

Spec = tuple[str, str]


def specs(selection: str) -> list[Spec]:
    """Return the specs a selection is written as, or refuse it.

    selection -- one spec, or several joined by ";"

    Return each spec as its first and last position, as written, in the
    order written; a single position is both. Raise ValueRefusalError
    for a selection that is not written as the syntax writes one.
    """
    found = []
    for spec in selection.split(_LIST):
        first, separator, last = spec.partition(_RANGE)
        if not separator:
            last = first
        if not (_written(first) and _written(last)):
            raise _refusal.ValueRefusalError(f"not a selection: {selection!r}")
        found.append((first, last))
    return found


def of(specs: list[Spec], count: int) -> list[int]:
    """Return the positions specs name, of so many.

    specs -- what specs returned for a selection
    count -- how many there are to choose from

    Return the positions in the order the specs are written, a position
    named twice given twice. RFC 7111, 4.2. Semantics of Fragment
    Identifiers: a single selection of a non-existing row is ignored; a
    range extends only to the actual size; a range that selects
    inversely is ignored; each specification is processed
    independently.
    """
    positions = []
    for first, last in specs:
        start = max(_position(first, count), 1)
        end = min(_position(last, count), count)
        positions.extend(range(start, end + 1))
    return positions


def selection(positions: list[int]) -> str:
    """Return the selection that names positions, in their order.

    positions -- positions from 1, in the order to name them

    Return each run of consecutive positions as a range, the specs
    joined by ";", and the empty text for no positions. RFC 7111, 3.
    Fragment Identification Syntax: singlespec = position [ "-"
    position ].
    """
    runs: list[list[int]] = []
    for position in positions:
        if runs and position == runs[-1][1] + 1:
            runs[-1][1] = position
        else:
            runs.append([position, position])
    return _LIST.join(
        str(first) if first == last else f"{first}{_RANGE}{last}"
        for first, last in runs
    )


def _written(text: str) -> bool:
    """Return whether a text is a position: a number, or "*".

    text -- the position as written
    """
    return text == _LAST or _NUMBER.fullmatch(text) is not None


def _position(text: str, count: int) -> int:
    """Return the position a text names: a number, or the last for "*".

    text -- the position as written
    count -- how many there are to choose from

    Return count + 1 for a number of more digits than count has. RFC
    7111, 4.2. Semantics of Fragment Identifiers: rows are counted from
    one, and "*" refers to the last row or column; a position beyond
    the size does not exist.
    """
    if text == _LAST:
        return count
    digits = text.lstrip("0")
    if len(digits) > len(str(count)):
        return count + 1
    return int(digits or "0")
