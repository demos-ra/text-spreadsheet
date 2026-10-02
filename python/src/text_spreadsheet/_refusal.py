"""What a refusal is: a call the tool cannot answer, and why.

MCP, server/tools Error Handling: tool execution errors "contain
actionable feedback that language models can use to self-correct and
retry with adjusted parameters".

Classes:
RefusalError -- a call the tool cannot answer, with the reason
ValueRefusalError -- a refusal of a pathname, a selection, a filter or
    a file's contents, as ValueError
LookupRefusalError -- a refusal of a file whose extension names no
    format, as LookupError
OSRefusalError -- a refusal of a file or directory that cannot be
    read, as OSError

Functions:
of -- return the refusal an error of what a call names is
"""

__all__ = [
    "RefusalError",
    "ValueRefusalError",
    "LookupRefusalError",
    "OSRefusalError",
    "of",
]


class RefusalError(Exception):
    """A call the tool cannot answer, with the reason."""


class ValueRefusalError(RefusalError, ValueError):
    """A refusal of a pathname, selection, filter or file's contents."""


class LookupRefusalError(RefusalError, LookupError):
    """A refusal of a file whose extension names no format."""


class OSRefusalError(RefusalError, OSError):
    """A refusal of a file or directory that cannot be read."""


def of(error: OSError | LookupError | ValueError) -> RefusalError:
    """Return the refusal an error of what a call names is.

    error -- an error raised reading, finding or converting a file

    Return the refusal of the same kind, with the same reason.
    """
    if isinstance(error, OSError):
        return OSRefusalError(str(error))
    if isinstance(error, LookupError):
        return LookupRefusalError(str(error))
    return ValueRefusalError(str(error))
