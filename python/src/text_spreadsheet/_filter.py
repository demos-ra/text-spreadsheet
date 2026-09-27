"""How a filter is written, and which records it selects.

Functions:
compile -- return the query a filter is, or refuse it
matches -- return the positions of the records a query selects
"""

__all__ = ["compile", "matches"]

import jsonpath_rfc9535
from jsonpath_rfc9535.segments import JSONPathChildSegment
from jsonpath_rfc9535.selectors import FilterSelector

# RFC 9535, 2.3.5.1. Syntax: filter-selector = "?" S logical-expr.
# 2.3.5. Filter Selector: the filter expression receives the node of
# each array element, the current node (@).
_OPEN = "$[?"
_CLOSE = "]"


def compile(filter: str) -> jsonpath_rfc9535.JSONPathQuery:
    """Return the query a filter is, or refuse it.

    filter -- an RFC 9535 logical-expr, the text after "?"

    Raise ValueError for a filter that is not well-formed and valid, or
    that is not exactly one filter selector. RFC 9535, 2.1. Overview: an
    implementation MUST raise an error for any query that is not
    well-formed and valid; 4.2. Attack Vectors on How JSONPath Queries
    Are Formed: values that form a query need to be validated.
    """
    try:
        query = jsonpath_rfc9535.compile(_OPEN + filter + _CLOSE)
    except jsonpath_rfc9535.JSONPathError as error:
        raise ValueError(f"not a filter: {error}") from error
    if not _one_filter(query):
        raise ValueError(f"not a filter: {filter!r}")
    return query


def matches(
    query: jsonpath_rfc9535.JSONPathQuery, records: list[list[str]]
) -> list[int]:
    """Return the positions of the records a query selects, from 1.

    query -- a query compile returned
    records -- the records of one sheet

    RFC 9535, 2.3.5.2. Semantics: children of an array are ordered by
    their position in the array.
    """
    return [node.location[0] + 1 for node in query.finditer(records)]


def _one_filter(query: jsonpath_rfc9535.JSONPathQuery) -> bool:
    """Return whether a query is one segment of one filter selector.

    query -- a compiled query
    """
    if len(query.segments) != 1:
        return False
    segment = query.segments[0]
    return (
        isinstance(segment, JSONPathChildSegment)
        and len(segment.selectors) == 1
        and isinstance(segment.selectors[0], FilterSelector)
    )
