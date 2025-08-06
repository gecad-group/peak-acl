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
peak_acl.events
===============
High-level structures for routing inbound HTTP-MTP messages.

End users (agents) only deal with :class:`MsgEvent`, which bundles the original
``Envelope`` and ``AclMessage`` plus a classified ``kind`` and a decoded
``payload``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Any

from ..message.aid import AgentIdentifier
from ..message.envelope import Envelope
from ..message.acl import AclMessage

# --------------------------------------------------------------------------- #
# Kind discriminator for runtime-classified messages.
# --------------------------------------------------------------------------- #
Kind = Literal[
    "df",
    "df-done",
    "df-failure",
    "df-result",
    "df-not-understood",
    "ext-sl0",
    "ext-raw",
]


# --------------------------------------------------------------------------- #
# MsgEvent
# --------------------------------------------------------------------------- #
@dataclass
class MsgEvent:
    """Runtime-classified message wrapper.

    Attributes
    ----------
    env :
        Original transport envelope (sender/receiver, date, etc.).
    acl :
        Parsed ACL message.
    sender :
        Convenience alias for ``env.from_``.
    kind :
        Classification label (see :data:`Kind`).
    payload :
        Decoded payload (e.g., ``Done`` / ``Failure`` / list of ADs / raw str).

    Notes
    -----
    Additional helpers (e.g., ``reply()``) can be added later without breaking
    existing code that treats this as a simple data container.
    """

    env: Envelope
    acl: AclMessage
    sender: AgentIdentifier  # = env.from_
    kind: Kind
    payload: Any  # Done / Failure / list[AD] / str / etc.
