# MIT License
# Copyright (c) 2025 Santiago Bossa
# See LICENSE file in the project root for full license text.

# peak_acl/conversation.py
"""
Conversation Manager – FIPA Request-like

Creates and tracks request-style conversations:

* Build with ``send_request()``
* Keeps a map: ``conversation_id -> _Conversation``
* Update state by calling :meth:`on_message` for every inbound ACL
* Returns futures/callbacks that agents can ``await``

Supported flow:
    REQUEST → {AGREE | REFUSE} → {INFORM | FAILURE}
"""

from __future__ import annotations

import asyncio
import secrets
import logging
from dataclasses import dataclass, field
from typing import Dict, Optional, Callable, Awaitable

from .message.aid import AgentIdentifier
from .message.acl import AclMessage
from . import sl0  # serialize SL0 payloads

_log = logging.getLogger("peak_acl.conversation")


# ---------------------------------------------------------------------- #
# Conversation state container
# ---------------------------------------------------------------------- #
@dataclass
class _Conversation:
    """Internal state holder for a single conversation."""
    conv_id: str
    future: asyncio.Future
    state: str = "pending"  # pending → {agreed|refused} → done
    request_msg: AclMessage | None = None
    reply_agree_refuse: AclMessage | None = None


# ---------------------------------------------------------------------- #
# Manager
# ---------------------------------------------------------------------- #
class ConversationManager:
    """Lightweight manager for the FIPA-Request interaction protocol."""

    def __init__(self, send_fn: Callable[[AclMessage, str], Awaitable[None]]):
        """
        Parameters
        ----------
        send_fn :
            Low-level function used to actually send a fully assembled ACL
            message: ``send_fn(msg, url)``.
        """
        self._convs: Dict[str, _Conversation] = {}
        self._send_fn = send_fn

    # ------------------------------------------------------------------ #
    async def send_request(
        self,
        *,
        sender: AgentIdentifier,
        receiver: AgentIdentifier,
        content,  # str | SL0 object
        language: str = "fipa-sl0",
        ontology: str = "default",
        protocol: str = "fipa-request",
        url: Optional[str] = None,
    ):
        """Send a REQUEST and return a Future resolving to INFORM/FAILURE.

        Parameters
        ----------
        sender, receiver :
            Agent identifiers for ACL ``sender`` / ``receivers`` slots.
        content :
            Either a raw string or an SL0 object (serialized if not str).
        language, ontology, protocol :
            ACL meta fields (defaults target FIPA-Request + SL0).
        url :
            Transport destination, passed to ``send_fn``.

        Returns
        -------
        asyncio.Future
            Await to get the final reply message (``INFORM`` or ``FAILURE``).
            If the first reply is ``REFUSE``, the future is resolved immediately
            with that message.

        Notes
        -----
        * Conversation ID is generated via `_gen_conv_id()`.
        * The future is stored in ``_convs`` until completion.
        """
        conv_id = _gen_conv_id(sender)
        if isinstance(content, str):
            content_str = content
        else:
            content_str = sl0.dumps(content)

        req = AclMessage(
            performative="request",
            sender=sender,
            receivers=[receiver],
            content=content_str,
            language=language,
            ontology=ontology,
            protocol=protocol,
            conversation_id=conv_id,
            reply_with=conv_id + ".req",
        )

        fut: asyncio.Future = asyncio.get_event_loop().create_future()
        self._convs[conv_id] = _Conversation(conv_id, fut, request_msg=req)

        await self._send_fn(req, url)  # fire REQUEST
        return fut  # await fut → AclMessage

    # ------------------------------------------------------------------ #
    def on_message(self, acl: AclMessage):
        """Feed every inbound ACL here; ignores unrelated conversations.

        Parameters
        ----------
        acl :
            Incoming message to be matched against tracked conversations.
        """
        cid = acl.conversation_id
        if not cid or cid not in self._convs:
            return

        conv = self._convs[cid]
        perf = acl.performative_upper

        # 1st reply → AGREE or REFUSE
        if conv.state == "pending":
            if perf in {"AGREE", "REFUSE"}:
                conv.reply_agree_refuse = acl
                conv.state = "agreed" if perf == "AGREE" else "refused"
                if perf == "REFUSE" and not conv.future.done():
                    conv.future.set_result(acl)
            return

        # 2nd reply → INFORM/FAILURE (or after REFUSE there's nothing else)
        if conv.state in {"agreed", "refused"}:
            if perf in {"INFORM", "FAILURE"}:
                if not conv.future.done():
                    conv.future.set_result(acl)
                conv.state = "done"
                del self._convs[cid]


# ---------------------------------------------------------------------- #
# Helpers
# ---------------------------------------------------------------------- #
def _gen_conv_id(sender: AgentIdentifier) -> str:
    """Generate a unique conversation id using the sender name + random hex."""
    rnd = secrets.token_hex(8)
    return f"{sender.name}{rnd}"
