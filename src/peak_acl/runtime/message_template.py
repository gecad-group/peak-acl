# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2025 Santiago Bossa
#
# This file is part of peak-acl.
#
# peak-acl is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# peak-acl is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with peak-acl.  If not, see the LICENSE file in the project root.

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
