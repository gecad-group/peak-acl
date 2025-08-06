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

# src/peak_acl/visitor.py
"""ANTLR visitor → :class:`AclMessage` (full FIPA model).

Walks the parse tree produced by ``ACLParser`` and builds an :class:`AclMessage`
instance. Nested messages (e.g., ``agent-identifier`` inside slots) are kept as
generic ``AclMessage`` objects for later coercion by helper functions.
"""

from __future__ import annotations

from typing import Any, Dict, Tuple

from ..generated.ACLVisitor import ACLVisitor
from ..generated.ACLParser import ACLParser

from ..message.acl import AclMessage
from .types import QuotedStr  # keep compatibility
from .parse_helpers import to_aid, to_aid_list, to_datetime


# Slots allowed at root level (case-insensitive)
ALLOWED_ROOT = {
    "sender",
    "receiver",
    "reply-to",
    "content",
    "language",
    "encoding",
    "ontology",
    "protocol",
    "conversation-id",
    "reply-with",
    "in-reply-to",
    "reply-by",
}

# Minimal mandatory slots by performative
MANDATORY_ROOT = {
    "inform": {"content"},
    "request": {"content"},
}


class MessageBuilder(ACLVisitor):
    """
    Visits the parse tree produced by ``ACLParser`` and builds a complete
    :class:`AclMessage`.

    Uses ``_depth`` to distinguish the root message from nested ones
    (AIDs, actions, etc.): depth==1 → root.
    """

    def __init__(self, raw_text: str) -> None:
        super().__init__()
        self._depth = 0
        self._raw_text = raw_text

    # --------------------------- message ----------------------------------- #
    def visitACLmessage(self, ctx: ACLParser.ACLmessageContext) -> AclMessage:
        """Build an ``AclMessage`` from the ``ACLmessage`` rule."""
        self._depth += 1
        try:
            perf = ctx.performative().SYMBOL().getText()
            perf_l = perf.lower()

            # Collect params
            params: Dict[str, Any] = {}
            for p_ctx in ctx.param():
                k, v = self.visit(p_ctx)
                params[k] = v

            # Root → structured AclMessage
            if self._depth == 1:
                msg = AclMessage(performative=perf_l, raw_text=self._raw_text)

                missing = MANDATORY_ROOT.get(perf_l, set()) - params.keys()
                if missing:
                    raise ValueError(f"{perf_l} precisa de: {', '.join(missing)}")

                for name, val in params.items():
                    lname = name.lower()
                    if lname == "sender":
                        msg.sender = to_aid(val)
                    elif lname == "receiver":
                        msg.receivers.extend(to_aid_list(val))
                    elif lname == "reply-to":
                        msg.reply_to.extend(to_aid_list(val))
                    elif lname == "content":
                        msg.content = _coerce_content(val)
                    elif lname == "language":
                        msg.language = str(val)
                    elif lname == "encoding":
                        msg.encoding = str(val)
                    elif lname == "ontology":
                        msg.ontology = str(val)
                    elif lname == "protocol":
                        msg.protocol = str(val)
                    elif lname == "conversation-id":
                        msg.conversation_id = str(val)
                    elif lname == "reply-with":
                        msg.reply_with = str(val)
                    elif lname == "in-reply-to":
                        msg.in_reply_to = str(val)
                    elif lname == "reply-by":
                        msg.reply_by = to_datetime(val)
                    else:
                        # Extensions (X-*)
                        msg.user_params[lname] = val
                return msg

            # Nested message → return a generic AclMessage (used for AID etc.)
            return AclMessage(performative=perf_l, user_params=params)

        finally:
            self._depth -= 1

    # ----------------------- :name value ------------------------------------ #
    def visitACLparam(self, ctx: ACLParser.ACLparamContext) -> Tuple[str, Any]:
        """Return ``(name, value)`` for a slot; leniency for unknown root slots."""
        name = ctx.SYMBOL().getText()
        if self._depth == 1:
            lname = name.lower()
            if lname not in ALLOWED_ROOT and not lname.startswith("x-"):
                # silently accept for robustness (could raise if strict)
                pass
        value = self.visit(ctx.value())
        return name, value

    # ----------------------- values ----------------------------------------- #
    def visitAtom(self, ctx: ACLParser.AtomContext):
        """Symbol atom → plain string."""
        return ctx.SYMBOL().getText()

    def visitString(self, ctx: ACLParser.StringContext):
        """STRING token → QuotedStr (keeps original quoting intent)."""
        raw = ctx.STRING().getText()  # includes quotes
        return QuotedStr(bytes(raw[1:-1], "utf-8").decode("unicode_escape"))

    def visitNestedMessage(self, ctx: ACLParser.NestedMessageContext):
        """Nested ACL message → visit recursively."""
        return self.visit(ctx.message())

    def visitListValue(self, ctx: ACLParser.ListValueContext):
        """List of values → Python list."""
        return [self.visit(v) for v in ctx.value()]


# --------------------------------------------------------------------------- #
# Local helpers
# --------------------------------------------------------------------------- #
def _coerce_content(val: Any):
    """
    Convert the :content slot to a friendlier form:

    - QuotedStr → str
    - AclMessage → keep object (useful for AIDs/actions)
    - list      → list stays list (upstream code may stringify)
    - atom      → str
    """
    if isinstance(val, QuotedStr):
        return str(val)
    return val
