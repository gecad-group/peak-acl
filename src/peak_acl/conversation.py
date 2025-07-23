# peak_acl/conversation.py
"""
Conversation Manager – FIPA Request‑like

• Cria‑se com send_request()
• Mantém mapa conv_id  ->  Conversation
• Actualiza‑se chamando .on_message(env, acl)
• Gera callbacks/futuros que o agente pode await‑ar

Suporta:
    REQUEST → {AGREE|REFUSE} → {INFORM|FAILURE}
"""

from __future__ import annotations
import asyncio, secrets, logging
from dataclasses import dataclass, field
from typing import Dict, Optional, Callable, Awaitable

from .message.aid import AgentIdentifier
from .message.acl import AclMessage
from . import sl0                                # para serializar payloads

_log = logging.getLogger("peak_acl.conversation")


# ---------------------------------------------------------------------- #
#  Conversation state
# ---------------------------------------------------------------------- #
@dataclass
class _Conversation:
    conv_id: str
    future: asyncio.Future
    state: str = "pending"          # pending → {agreed|refused} → done
    request_msg: AclMessage | None = None
    reply_agree_refuse: AclMessage | None = None


# ---------------------------------------------------------------------- #
#  Manager
# ---------------------------------------------------------------------- #
class ConversationManager:
    """Um gestor “leve” só para o protocolo Request."""
    def __init__(self, send_fn: Callable[[AclMessage, str], Awaitable[None]]):
        """
        send_fn(msg, url)  – função low‑level usada para enviar ACL já montada
        """
        self._convs: Dict[str, _Conversation] = {}
        self._send_fn = send_fn

    # ------------------------------------------------------------------ #
    async def send_request(
        self,
        *,
        sender: AgentIdentifier,
        receiver: AgentIdentifier,
        content,                       # str | SL0 object
        language: str = "fipa-sl0",
        ontology: str = "default",
        protocol: str = "fipa-request",
        url: Optional[str] = None,
    ):
        """Envia REQUEST e devolve um *future* que resolve com INFORM/FAILURE."""
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

        await self._send_fn(req, url)            # dispara REQUEST
        return fut                                # await fut → AclMessage

    # ------------------------------------------------------------------ #
    def on_message(self, acl: AclMessage):
        """Chama‑se para TODAS as mensagens inbound; ignora as não‑relacionadas."""
        cid = acl.conversation_id
        if not cid or cid not in self._convs:
            return

        conv = self._convs[cid]
        perf = acl.performative_upper

        # 1ª resposta → AGREE ou REFUSE
        if conv.state == "pending":
            if perf in {"AGREE", "REFUSE"}:
                conv.reply_agree_refuse = acl
                conv.state = "agreed" if perf == "AGREE" else "refused"
                if perf == "REFUSE" and not conv.future.done():
                    conv.future.set_result(acl)
            return

        # 2ª resposta → INFORM/FAILURE (ou caso especial se tiver havido REFUSE)
        if conv.state in {"agreed", "refused"}:
            if perf in {"INFORM", "FAILURE"}:
                if not conv.future.done():
                    conv.future.set_result(acl)
                conv.state = "done"
                del self._convs[cid]


# ---------------------------------------------------------------------- #
# helpers
# ---------------------------------------------------------------------- #
def _gen_conv_id(sender: AgentIdentifier) -> str:
    rnd = secrets.token_hex(8)
    return f"{sender.name}{rnd}"
