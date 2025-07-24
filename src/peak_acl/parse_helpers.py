# MIT License
# Copyright (c) 2025 Santiago Bossa
# See LICENSE file in the project root for full license text.

# src/peak_acl/parse_helpers.py
"""
Auxiliary functions used by the ANTLR visitor to convert parsed values
(Atoms, ListValue, NestedMessage) into FIPA-friendly structures:
``AgentIdentifier``, lists of AIDs, ``reply-by`` datetimes, etc.

Public API
----------
- :func:`to_aid`
- :func:`to_aid_list`
- :func:`to_datetime`
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable, List, Optional

from .message.aid import AgentIdentifier
from .message.acl import AclMessage


# --------------------------------------------------------------------------- #
# Small predicates
# --------------------------------------------------------------------------- #
def _is_list(v: Any) -> bool:
    """Return True if *v* is a Python list (visitor output form)."""
    return isinstance(v, list)


def _is_acl(v: Any) -> bool:
    """Return True if *v* is an :class:`AclMessage` (nested message)."""
    return isinstance(v, AclMessage)


# --------------------------------------------------------------------------- #
# AID conversion
# --------------------------------------------------------------------------- #
def to_aid(value: Any) -> AgentIdentifier:
    """Convert a nested ``(agent-identifier ...)`` ACL message to ``AgentIdentifier``.

    Expected form (already parsed into an ``AclMessage``):

    .. code-block:: lisp

        (agent-identifier :name foo@host:port/JADE
                          :addresses (sequence http://... http://...))

    Raises
    ------
    TypeError
        If *value* is not an ``AclMessage``.
    ValueError
        If the nested message is not ``agent-identifier`` or missing ``:name``.
    """
    if not _is_acl(value):
        raise TypeError(f"Esperava message agent-identifier; recebi {type(value)!r}")

    msg: AclMessage = value
    if msg.performative.lower() != "agent-identifier":
        raise ValueError("Nested message não é agent-identifier")

    name = None
    addrs: List[str] = []

    # Slots live in msg.user_params; msg.content is unused here
    for k, v in msg.user_params.items():
        lk = k.lower()
        if lk == "name":
            name = str(v)
        elif lk == "addresses":
            addrs = _sequence_to_strings(v)
        # resolvers ignored for now

    if name is None:
        raise ValueError("agent-identifier sem :name")

    return AgentIdentifier(name, addrs)


def _sequence_to_strings(v: Any) -> List[str]:
    """Convert a parsed ``(sequence ...)`` structure to a list of strings.

    The visitor usually produces ``['sequence', 'url1', 'url2', ...]``.
    If *v* is not a list (JADE sometimes sends a single URL), wrap it.
    """
    if not _is_list(v):
        return [str(v)]
    if len(v) >= 2 and isinstance(v[0], str) and v[0].lower() == "sequence":
        return [str(x) for x in v[1:]]
    # Already a plain list of URLs
    return [str(x) for x in v]


# --------------------------------------------------------------------------- #
# List of AIDs (receiver, reply-to)
# --------------------------------------------------------------------------- #
def to_aid_list(value: Any) -> List[AgentIdentifier]:
    """Convert ``(set <aid> <aid> ...)`` or a single AID into a Python list.

    JADE tolerates a single AID without a ``(set ...)`` wrapper.
    """
    if _is_acl(value):
        return [to_aid(value)]
    if _is_list(value):
        vals = value
        if vals and isinstance(vals[0], str) and vals[0].lower() == "set":
            vals = vals[1:]
        return [to_aid(v) for v in vals]
    raise TypeError(f"Não consigo converter {value!r} em lista de AIDs")


# --------------------------------------------------------------------------- #
# reply-by datetime
# --------------------------------------------------------------------------- #
def to_datetime(v: Any) -> Optional[datetime]:
    """Parse common FIPA/ISO date strings into ``datetime`` or return ``None``.

    JADE usually emits ISO-like formats, e.g. ``20250715T103845`` (or with ``Z``).

    Tried patterns (in order):
        ``%Y%m%dT%H%M%S`` • ``%Y%m%dZ%H%M%S`` • ``%Y-%m-%dT%H:%M:%S`` • ``%Y%m%d``

    Returns
    -------
    datetime | None
        Parsed naive ``datetime`` (no tzinfo) or ``None`` if parsing fails.
    """
    if v is None:
        return None
    s = str(v).strip().strip('"')
    for fmt in ("%Y%m%dT%H%M%S", "%Y%m%dZ%H%M%S", "%Y-%m-%dT%H:%M:%S", "%Y%m%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    return None
