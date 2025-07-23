# peak_acl/runtime.py
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import (
    Sequence, Tuple, Optional, Iterable, Union, AsyncIterator, Callable,
)

import aiohttp.web

from .message.aid import AgentIdentifier
from .message.acl import AclMessage
from .transport.http_mtp import HttpMtpServer, start_server
from .transport.http_client import HttpMtpClient
from . import df_manager, sl0
from . import event, router
from .conversation import ConversationManager   #  <-- novo import

# ------------------------------------------------------------------ #
# util
# ------------------------------------------------------------------ #
def _first_url(ai: AgentIdentifier) -> str:
    if not ai.addresses:
        raise ValueError(f"AID sem endereço HTTP: {ai}")
    return ai.addresses[0]


# ------------------------------------------------------------------ #
# Endpoint de comunicação (server inbound + client outbound)
# ------------------------------------------------------------------ #
@dataclass
class CommEndpoint(AsyncIterator[event.MsgEvent]):
    """Objecto principal de I/O para o agente."""

    # --- campos base ------------------------------------------------- #
    my_aid: AgentIdentifier
    inbox: asyncio.Queue[Tuple[object, AclMessage]]  # (Envelope, AclMessage)
    client: HttpMtpClient
    server: HttpMtpServer
    runner: aiohttp.web.AppRunner
    site: aiohttp.web.TCPSite

    # --- opcionais --------------------------------------------------- #
    df_aid: Optional[AgentIdentifier] = None
    conv_mgr: Optional[ConversationManager] = None   # <– gestor de conversas

    # ------------------- DF helpers ---------------------------------- #
    async def register_df(
        self,
        df_aid: AgentIdentifier,
        services: Iterable[Tuple[str, str]],
        *,
        df_url: str | None = None,
        languages=(), ontologies=(), protocols=(), ownership=(),
    ):
        await df_manager.register(
            my_aid=self.my_aid,
            df_aid=df_aid,
            services=services,
            languages=languages,
            ontologies=ontologies,
            protocols=protocols,
            ownership=ownership,
            http_client=self.client,
            df_url=df_url,
        )

    async def deregister_df(
        self,
        df_aid: AgentIdentifier | None = None,
        *,
        df_url: str | None = None,
    ):
        df_ai = df_aid or self.df_aid
        if df_ai is None:
            raise ValueError("deregister_df() sem df_aid definido.")
        await df_manager.deregister(
            my_aid=self.my_aid,
            df_aid=df_ai,
            http_client=self.client,
            df_url=df_url,
        )

    async def search_df(
        self,
        *,
        service_name: str | None = None,
        service_type: str | None = None,
        max_results: int | None = None,
        df_aid: AgentIdentifier | None = None,
        df_url: str | None = None,
    ):
        df_ai = df_aid or self.df_aid
        if df_ai is None:
            raise ValueError("search_df() sem df_aid definido.")
        await df_manager.search_services(
            my_aid=self.my_aid,
            df_aid=df_ai,
            service_name=service_name,
            service_type=service_type,
            max_results=max_results,
            http_client=self.client,
            df_url=df_url,
        )

    # ------------------- ACL genérico -------------------------------- #
    async def send_acl(
        self,
        *,
        to: Union[AgentIdentifier, Iterable[AgentIdentifier]],
        performative: str,
        content: str | object | None = None,
        language: str | None = None,
        ontology: str | None = None,
        protocol: str | None = None,
        conversation_id: str | None = None,
        reply_with: str | None = None,
        in_reply_to: str | None = None,
        reply_by: str | None = None,
    ) -> AclMessage:
        """
        Envia uma mensagem ACL genérica.

        `content`:
          • str          → usado tal-e-qual
          • outro object → serializado via sl0.dumps()
          • None         → sem slot :content
        """
        # normaliza recetores
        receivers = [to] if isinstance(to, AgentIdentifier) else list(to)
        if not receivers:
            raise ValueError("send_acl() precisa de pelo menos 1 recetor")

        # serializa conteúdo
        content_str: str | None
        if content is None:
            content_str = None
        elif isinstance(content, str):
            content_str = content
        else:
            content_str = sl0.dumps(content)

        msg = AclMessage(
            performative=performative,
            sender=self.my_aid,
            receivers=receivers,
            content=content_str,
            language=language,
            ontology=ontology,
            protocol=protocol,
            conversation_id=conversation_id,
            reply_with=reply_with,
            in_reply_to=in_reply_to,
            reply_by=reply_by,
        )

        # envia POST por recetor
        for r in receivers:
            await self.client.send(r, self.my_aid, msg, _first_url(r))
        return msg

    # ------------------- Conversation proxy -------------------------- #
    async def send_request(self, **kw):
        """
        Envia REQUEST e devolve (agree|refuse, inform|failure).

        Wrapper sobre ConversationManager.
        """
        if self.conv_mgr is None:
            raise RuntimeError("ConversationManager não inicializado.")
        return await self.conv_mgr.send_request(sender=self.my_aid, **kw)

    # ----------------------- iterator interface ---------------------- #
    def __aiter__(self):
        return self

    async def __anext__(self) -> event.MsgEvent:  # noqa: D401
        """Bloqueia até chegar uma mensagem e devolve MsgEvent."""
        env, acl = await self.inbox.get()
        kind, payload = router.classify_message(env, acl, self.df_aid)
        # entrega também ao ConversationManager
        if self.conv_mgr:
            self.conv_mgr.feed(env.from_, acl)
        return event.MsgEvent(env, acl, env.from_, kind, payload)

    # ------------------------------------------------------------------ #
    async def close(self):
        await self.runner.cleanup()
        await self.client.close()


# ------------------------------------------------------------------ #
# Arrancar endpoint
# ------------------------------------------------------------------ #
async def start_endpoint(
    *,
    my_aid: AgentIdentifier,
    bind_host: str = "0.0.0.0",
    auto_register: bool = False,
    df_aid: Optional[AgentIdentifier] = None,
    services: Optional[Sequence[Tuple[str, str]]] = None,
    http_client: Optional[HttpMtpClient] = None,
    loop=None,
) -> CommEndpoint:
    """
    Cria server inbound + cliente outbound + inbox.
    Se `auto_register` estiver True, envia REQUEST register ao DF.
    """
    # --- resolve porta a partir do 1º endereço HTTP publicado -------- #
    from urllib.parse import urlparse

    u = urlparse(my_aid.addresses[0])
    port = u.port or 80

    client = http_client or HttpMtpClient()
    server, runner, site = await start_server(
        on_message=None,
        bind_host=bind_host,
        port=port,
        loop=loop,
    )

    ep = CommEndpoint(
        my_aid=my_aid,
        inbox=server.inbox,
        client=client,
        server=server,
        runner=runner,
        site=site,
        df_aid=df_aid,
    )

    # -------- instancia ConversationManager -------------------------- #
    async def _low_level_send(msg: AclMessage, dst_url: str):
        """Função de envio utilizada pelo ConversationManager."""
        await client.send(msg.receivers[0], my_aid, msg, dst_url)

    ep.conv_mgr = ConversationManager(send_func=_low_level_send)

    # ---------------- auto-register DF ------------------------------- #
    if auto_register:
        if df_aid is None:
            raise ValueError("auto_register=True mas df_aid=None")
        await ep.register_df(
            df_aid=df_aid,
            services=services or [],
            df_url=df_aid.addresses[0],
        )

    return ep
