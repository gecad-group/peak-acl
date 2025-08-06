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
FIPA-ACL message model for the *peak_acl* package.

This module defines :class:`AclMessage`, a Python representation of a FIPA
Agent Communication Language (ACL) message fully compatible with JADE agents.
It exposes all canonical ACL slots (``performative``, ``sender``, ``receiver``,
``reply-to`` …), supports multiple receivers / reply-to addresses, and offers
*dict-like* access helpers so that existing code can use ``msg["content"]``,
``"slot" in msg`` or ``msg.get()`` transparently.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .aid import AgentIdentifier

# --------------------------------------------------------------------------- #
# _norm_performative
# --------------------------------------------------------------------------- #
def _norm_performative(p: str) -> str:
    """Return a FIPA-compliant performative name (UPPERCASE, hyphen-separated).

    Examples
    --------
    >>> _norm_performative("inform_ref")
    'INFORM-REF'
    """
    return p.strip().upper().replace("_", "-")


# --------------------------------------------------------------------------- #
# AclMessage
# --------------------------------------------------------------------------- #
@dataclass
class AclMessage:
    """In-memory representation of a FIPA-ACL message.

    Attributes
    ----------
    performative :
        Speech-act verb (e.g. ``"INFORM"``, ``"REQUEST"``).
    sender :
        Identity of the agent originating the message.
    receivers :
        Zero or more intended recipients.
    reply_to :
        Alternate address(es) the sender wants replies to go to.
    content :
        Application payload – free-form string/bytes/object or nested
        :class:`AclMessage`.
    language, encoding, ontology, protocol :
        Optional meta-data slots defined by the FIPA spec.
    conversation_id, reply_with, in_reply_to, reply_by :
        Dialogue control & correlation fields.
    user_params :
        Extra non-standard ``X-*`` slots preserved round-trip.
    raw_text :
        Original text version (debug / logging aid).

    Notes
    -----
    The class implements minimal *dict-like* behavior so existing code can do::

        if "ontology" in msg:
            process(msg["ontology"])

    without breaking type safety for new code that uses attributes directly.
    """

    # ------------------------------------------------------------------ #
    # Core FIPA-ACL slots
    # ------------------------------------------------------------------ #
    performative: str

    # Agent addresses
    sender: Optional[AgentIdentifier] = None
    receivers: List[AgentIdentifier] = field(default_factory=list)
    reply_to: List[AgentIdentifier] = field(default_factory=list)

    # Payload & meta
    content: Optional[Any] = None  # str | bytes | object | AclMessage
    language: Optional[str] = None
    encoding: Optional[str] = None
    ontology: Optional[str] = None
    protocol: Optional[str] = None

    # Conversation control
    conversation_id: Optional[str] = None
    reply_with: Optional[str] = None
    in_reply_to: Optional[str] = None
    reply_by: Optional[datetime] = None

    # User-defined extension slots (X-*)
    user_params: Dict[str, Any] = field(default_factory=dict)

    # Raw text (useful during parsing / debugging)
    raw_text: Optional[str] = None

    # ------------------------------------------------------------------ #
    # Convenience helpers
    # ------------------------------------------------------------------ #
    def add_receiver(self, aid: AgentIdentifier) -> None:
        """Append *aid* to :py:attr:`receivers`."""
        self.receivers.append(aid)

    def add_reply_to(self, aid: AgentIdentifier) -> None:
        """Append *aid* to :py:attr:`reply_to`."""
        self.reply_to.append(aid)

    @property
    def performative_upper(self) -> str:
        """Return :py:attr:`performative` normalized per FIPA rules."""
        return _norm_performative(self.performative)

    # ------------------------------------------------------------------ #
    # dict-like compatibility layer
    # ------------------------------------------------------------------ #
    def __getitem__(self, key: str):
        """Allow ``value = msg["slot"]`` style access; raises *KeyError*."""
        k = key.lower()
        if k == "content":
            return self.content
        if k == "language":
            return self.language
        if k == "encoding":
            return self.encoding
        if k == "ontology":
            return self.ontology
        if k == "protocol":
            return self.protocol
        if k in ("conversation-id", "conversationid"):
            return self.conversation_id
        if k in ("reply-with", "replywith"):
            return self.reply_with
        if k in ("in-reply-to", "inreplyto"):
            return self.in_reply_to
        if k in ("reply-by", "replyby"):
            return self.reply_by
        # Fallback to user-defined params
        return self.user_params[k]

    def __setitem__(self, key: str, value: Any):
        """Allow ``msg["slot"] = value`` assignment semantics."""
        k = key.lower()
        if k == "content":
            self.content = value
        elif k == "language":
            self.language = value
        elif k == "encoding":
            self.encoding = value
        elif k == "ontology":
            self.ontology = value
        elif k == "protocol":
            self.protocol = value
        elif k in ("conversation-id", "conversationid"):
            self.conversation_id = value
        elif k in ("reply-with", "replywith"):
            self.reply_with = value
        elif k in ("in-reply-to", "inreplyto"):
            self.in_reply_to = value
        elif k in ("reply-by", "replyby"):
            self.reply_by = value
        else:
            self.user_params[k] = value

    # ------------------------------------------------------------------ #
    # Modern helpers
    # ------------------------------------------------------------------ #
    def get(self, key: str, default: Any = None):
        """dict.get() equivalent; returns *default* if *key* is absent."""
        try:
            return self[key]
        except KeyError:
            return default

    def __contains__(self, key: str) -> bool:
        """Enable ``"slot" in msg`` syntax."""
        try:
            self[key]
            return True
        except KeyError:
            return False
