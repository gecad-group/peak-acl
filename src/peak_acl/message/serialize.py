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

# src/peak_acl/serialize.py
"""
Serialize :class:`AclMessage` instances to JADE/FIPA-ACL compliant strings.

Key points
----------
* Builds the ``(PERFORMATIVE ... :slot value ...)`` syntax expected by JADE.
* Handles nested SL0 objects and even nested ``AclMessage`` instances.
* Includes a critical DF/JADE patch to wrap SL content with extra parentheses
  when needed (see comment in :func:`dumps`).
* ``user_params`` values are now escaped/quoted via ``_quote_val`` to avoid
  breaking the ACL syntax.

Public API
----------
- :func:`dumps`
"""

from __future__ import annotations

from typing import Any

from .acl import AclMessage
from .aid import AgentIdentifier
from ..sl import sl0  # import whole module to avoid circular imports


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _quote_val(v: Any) -> str:
    """Return a FIPA-safe string for values in ``user_params``."""
    # Keep numbers/bools unquoted
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, bool):
        return str(v).lower()
    s = str(v)
    s = s.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{s}"'


def _aid_to_fipa(aid: AgentIdentifier) -> str:
    """Return an ``agent-identifier`` SL string for *aid*.

    Example
    -------
    ``(agent-identifier :name bob :addresses (sequence http://...))``
    """
    addrs = " ".join(aid.addresses) if aid.addresses else ""
    seq = f"(sequence {addrs})" if addrs else "(sequence)"
    return f"(agent-identifier :name {aid.name} :addresses {seq})"


def _content_to_str(c: Any) -> str:
    """Serialize the ``content`` slot to a plain SL-compatible string.

    Supports:
    * SL0 AST objects (Action, Register, Done, etc.) via ``sl0.dumps``.
    * Nested :class:`AclMessage` via recursive :func:`dumps`.
    * Raw strings (unquoted unless already quoted).
    * Fallback to ``str(c)`` for everything else.
    """
    if isinstance(
        c,
        (
            sl0.Action,
            sl0.Register,
            sl0.Deregister,
            sl0.Modify,
            sl0.Search,
            sl0.Done,
            sl0.Failure,
            sl0.DfAgentDescription,
            sl0.ServiceDescription,
        ),
    ):
        return sl0.dumps(c)

    # Local import to avoid cycle at module import time
    from .acl import AclMessage  # noqa: WPS433 (local import by design)

    if isinstance(c, AclMessage):
        return dumps(c)

    if isinstance(c, str):
        # If already quoted, strip quotes so we'll re-escape later
        if len(c) >= 2 and c[0] == '"' and c[-1] == '"':
            return c[1:-1]
        return c

    return str(c)


# --------------------------------------------------------------------------- #
# Public serializer
# --------------------------------------------------------------------------- #
def dumps(msg: AclMessage) -> str:
    """Serialize an :class:`AclMessage` into a FIPA-ACL string.

    Parameters
    ----------
    msg :
        Message instance to serialize.

    Returns
    -------
    str
        JADE/FIPA-ACL compliant textual representation.

    Notes
    -----
    * **CRITICAL PATCH for DF/JADE**: if ``language`` starts with ``"fipa-sl"``,
      ensure the content is wrapped in an extra pair of parentheses unless it
      already starts with ``"(("``. This mirrors JADE's expectations.
    * ``user_params`` are escaped/quoted with ``_quote_val`` to keep output
      syntactically valid.
    """
    p = msg.performative_upper
    parts = [f"({p}"]

    if msg.sender:
        parts.append(f" :sender {_aid_to_fipa(msg.sender)}")

    if msg.receivers:
        recs = " ".join(_aid_to_fipa(a) for a in msg.receivers)
        parts.append(f" :receiver (set {recs})")

    if msg.reply_to:
        rts = " ".join(_aid_to_fipa(a) for a in msg.reply_to)
        parts.append(f" :reply-to (set {rts})")

    if msg.content is not None:
        c = _content_to_str(msg.content)

        # --- PATCH CRÍTICO PARA DF/JADE ---------------------------------
        if msg.language and msg.language.lower().startswith("fipa-sl"):
            stripped = c.lstrip()
            if not stripped.startswith("(("):
                c = f"({c})"
        # ----------------------------------------------------------------

        c = c.replace('"', '\\"')
        parts.append(f' :content "{c}"')

    if msg.language:
        parts.append(f" :language {msg.language}")
    if msg.encoding:
        parts.append(f" :encoding {msg.encoding}")
    if msg.ontology:
        parts.append(f" :ontology {msg.ontology}")
    if msg.protocol:
        parts.append(f" :protocol {msg.protocol}")
    if msg.conversation_id:
        parts.append(f" :conversation-id {msg.conversation_id}")
    if msg.reply_with:
        parts.append(f" :reply-with {msg.reply_with}")
    if msg.in_reply_to:
        parts.append(f" :in-reply-to {msg.in_reply_to}")
    if msg.reply_by:
        parts.append(f" :reply-by {msg.reply_by.strftime('%Y%m%dT%H%M%S')}")

    for k, v in msg.user_params.items():
        parts.append(f" :{k} {_quote_val(v)}")

    parts.append(")")
    return "".join(parts)
