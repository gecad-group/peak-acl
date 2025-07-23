"""
InboundDispatcher – roteia mensagens recebidas para callbacks
registrados com um MessageTemplate.
"""

from __future__ import annotations
import asyncio
from typing import Awaitable, Callable, List, Tuple

from .message_template import MessageTemplate
from .message.acl import AclMessage
from .message.aid import AgentIdentifier

# assinatura dos callbacks
Callback = Callable[[AgentIdentifier, AclMessage], Awaitable[None]]


class InboundDispatcher:
    def __init__(self) -> None:
        # lista de pares (template, callback)
        self._rules: List[Tuple[MessageTemplate, Callback]] = []

    # ----------------------------------------------------------- #
    def add(self, tmpl: MessageTemplate, cb: Callback) -> None:
        """Regista um novo handler."""
        self._rules.append((tmpl, cb))

    # ----------------------------------------------------------- #
    async def dispatch(self, sender: AgentIdentifier, acl: AclMessage) -> bool:
        """
        Procura o primeiro template que faça match; se encontrar agenda
        o callback (asyncio.create_task) e devolve True. Caso contrário
        devolve False.
        """
        for tmpl, cb in self._rules:
            if tmpl.match(acl):
                asyncio.create_task(cb(sender, acl))
                return True
        return False
