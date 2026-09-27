"""What a field can hold, and how text it cannot hold is written.

Functions:
holds -- return whether a field can hold a text
written -- return a text as a field holds it
"""

__all__ = ["holds", "written"]

# The draft, Grammar: field-char is any character except HTAB, LF, FF,
# and CR. The draft, Generators: a generator MUST NOT write a field
# that contains one.
_NOT_FIELD_CHARS = "\t\n\f\r"
_REPLACEMENT = "�"


def holds(text: str) -> bool:
    """Return whether a field can hold a text.

    text -- the text
    """
    return not any(char in _NOT_FIELD_CHARS for char in text)


def written(text: str) -> str:
    """Return a text as a field holds it.

    text -- the text

    Return it with each HTAB, LF, FF and CR as U+FFFD.
    """
    for char in _NOT_FIELD_CHARS:
        text = text.replace(char, _REPLACEMENT)
    return text
