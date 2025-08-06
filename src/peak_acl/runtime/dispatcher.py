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
InboundDispatcher – routes inbound ACL messages to callbacks registered
with a :class:`MessageTemplate`.

It stores (template, callback) pairs and, on dispatch, finds the first match,
schedules the callback with ``asyncio.create_task`` and returns ``True``.
If nothing matches, it returns ``False``.
"""

from __future__ import annotations

import asyncio
from typing import Awaitable, Callable, List, Tuple

from .message_template import MessageTemplate
from ..message.acl import AclMessage
from ..message.aid import AgentIdentifier

# Signature of registered callbacks
Callback = Callable[[AgentIdentifier, AclMessage], Awaitable[None]]


# --------------------------------------------------------------------------- #
# InboundDispatcher
# --------------------------------------------------------------------------- #
class InboundDispatcher:
    """Simple rule-based dispatcher for inbound ACL messages."""

    def __init__(self) -> None:
        # List of (template, callback) pairs; first match wins.
        self._rules: List[Tuple[MessageTemplate, Callback]] = []

    # ----------------------------------------------------------- #
    def add(self, tmpl: MessageTemplate, cb: Callback) -> None:
        """Register a new handler rule."""
        self._rules.append((tmpl, cb))

    # ----------------------------------------------------------- #
    async def dispatch(self, sender: AgentIdentifier, acl: AclMessage) -> bool:
        """Match the first template and schedule its callback.

        Parameters
        ----------
        sender :
            Sender AID (extracted upstream).
        acl :
            Inbound ACL message.

        Returns
        -------
        bool
            ``True`` if a rule matched (callback scheduled), else ``False``.

        Notes
        -----
        * Callbacks run in background tasks; exceptions inside them will be
          logged only if the callback handles them or the event loop has a
          task exception handler.
        * Rule order matters: the first matching template is chosen.
        """
        for tmpl, cb in self._rules:
            if tmpl.match(acl):
                asyncio.create_task(cb(sender, acl))
                return True
        return False
