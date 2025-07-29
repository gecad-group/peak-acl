# MIT License
# Copyright (c) 2025 Santiago Bossa
# See LICENSE file in the project root for full license text.

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
