# MIT License
# Copyright (c) 2025 Santiago Bossa
# See LICENSE file in the project root for full license text.

"""
MessageTemplate – simple JADE-like filter for ACL messages.

Allows matching over ``performative``, ``protocol`` and ``ontology`` fields.
"""

from __future__ import annotations

from typing import Optional

from ..message.acl import AclMessage


# --------------------------------------------------------------------------- #
# MessageTemplate
# --------------------------------------------------------------------------- #
class MessageTemplate:
    """Lightweight predicate for filtering :class:`AclMessage` objects.

    Parameters
    ----------
    performative :
        Target performative (case-insensitive). Stored uppercased.
    protocol :
        Target protocol string (case-insensitive). Stored lowercased.
    ontology :
        Target ontology string (case-insensitive). Stored lowercased.

    Notes
    -----
    * Uses ``__slots__`` to avoid per-instance ``__dict__`` (slightly lighter).
    * Only fields explicitly provided are checked; missing ones are ignored.
    """

    __slots__ = ("performative", "protocol", "ontology")

    def __init__(
        self,
        *,
        performative: Optional[str] = None,
        protocol: Optional[str] = None,
        ontology: Optional[str] = None,
    ):
        self.performative = performative.upper() if performative else None
        self.protocol = protocol.lower() if protocol else None
        self.ontology = ontology.lower() if ontology else None

    # --------------------------------------------------------------- #
    def match(self, acl: AclMessage) -> bool:
        """Return ``True`` if *acl* matches all defined template fields."""
        if self.performative and acl.performative_upper != self.performative:
            return False
        if self.protocol and (acl.protocol or "").lower() != self.protocol:
            return False
        if self.ontology and (acl.ontology or "").lower() != self.ontology:
            return False
        return True
