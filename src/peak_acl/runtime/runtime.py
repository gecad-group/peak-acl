# peak_acl/runtime.py
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
import contextlib
from typing import (
    Sequence, Tuple, Optional, Iterable, Union,
    AsyncIterator, Any,
)

import aiohttp.web

from ..message.aid import AgentIdentifier
from ..message.acl import AclMessage
from ..message.envelope import Envelope
from ..transport.http_mtp import HttpMtpServer, start_server
from ..transport.http_client import HttpMtpClient
from . import df_manager, event, router
from ..sl import sl0
from .dispatcher import InboundDispatcher, Callback
from .message_template import MessageTemplate
from .conversation import ConversationManager


# --------------------------------------------------------------------------- #
def _first_url(ai: AgentIdentifier) -> str:
    if not ai.addresses:
        raise ValueError(f"AID sem endereço HTTP: {ai}")
    return ai.addresses[0]


# --------------------------------------------------------------------------- #
@dataclass
class _RawMsg:                # só para a fila interna
    env: Envelope
    acl: AclMessage


# --------------------------------------------------------------------------- #
@dataclass
class CommEndpoint(AsyncIterator[event.MsgEvent]):
    """
    Endpoint = HTTP‑MTP server + client + helpers.

    * Usa callbacks via register_handler()
    * Continúa a suportar `async for evt in ep`
      (eventos ficam numa fila interna _events)
    """
    my_aid: AgentIdentifier
    inbox: asyncio.Queue                # (Envelope, AclMessage) do servidor
    client: HttpMtpClient
    server: HttpMtpServer
    runner: aiohttp.web.AppRunner
    site: aiohttp.web.TCPSite
    df_aid: Optional[AgentIdentifier] = field(default=None)

    # ponto 5
    dispatcher: InboundDispatcher = field(default_factory=InboundDispatcher)
    conv_mgr:   ConversationManager | None = None

    # fila de eventos para quem iterar sobre o endpoint
    _events: asyncio.Queue[event.MsgEvent] = field(
        default_factory=lambda: asyncio.Queue(maxsize=0)
    )
    _bg_task: Optional[asyncio.Task] = None

    # ---------------------------- DF helpers ------------------------------ #
    async def register_df(self, df_aid, services, *,
                          df_url=None, languages=(), ontologies=(),
                          protocols=(), ownership=()):
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

    async def search_df(self, *, service_name=None, service_type=None,
                        max_results=None, df_aid=None, df_url=None):
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

    async def deregister_df(self, df_aid=None, *, df_url=None):
        df_ai = df_aid or self.df_aid
        if df_ai is None:
            raise ValueError("deregister_df() sem df_aid definido.")
        await df_manager.deregister(
            my_aid=self.my_aid,
            df_aid=df_ai,
            http_client=self.client,
            df_url=df_url,
        )

    # ----------------------- envio ACL genérico -------------------------- #
    async def send_acl(
        self,
        *,
        to: Union[AgentIdentifier, Iterable[AgentIdentifier]],
        performative: str,
        content: Any = None,
        language: Optional[str] = None,
        ontology: Optional[str] = None,
        protocol: Optional[str] = None,
        conversation_id: Optional[str] = None,
        reply_with: Optional[str] = None,
        in_reply_to: Optional[str] = None,
        reply_by: Optional[str] = None,
    ) -> AclMessage:
        receivers = [to] if isinstance(to, AgentIdentifier) else list(to)
        if not receivers:
            raise ValueError("send_acl() sem receivers.")

        content_str = (
            None if content is None else
            content if isinstance(content, str) else
            sl0.dumps(content)
        )

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

        for r in receivers:
            await self.client.send(r, self.my_aid, msg, _first_url(r))
        return msg

    # ---------------------- açucar ConversationMgr ----------------------- #
    async def send_request(self, **kw):
        if not self.conv_mgr:
            raise RuntimeError("ConversationManager não inicializado.")
        return await self.conv_mgr.send_request(sender=self.my_aid, **kw)

    # ---------------------- handlers (ponto 5) --------------------------- #
    def register_handler(
        self,
        *,
        performative: str | None = None,
        protocol: str | None = None,
        ontology: str | None = None,
        cb: Callback,
    ):
        tmpl = MessageTemplate(
            performative=performative,
            protocol=protocol,
            ontology=ontology,
        )
        self.dispatcher.add(tmpl, cb)

    # ---------------------- iterator interface --------------------------- #
    def __aiter__(self):
        return self

    async def __anext__(self) -> event.MsgEvent:
        return await self._events.get()

    # ---------------------- background loop ----------------------------- #
    async def _pump(self):
        """Corre em background: esvazia inbox e trata callbacks."""
        while True:
            env, acl = await self.inbox.get()

            # 1) callbacks registados
            handled = await self.dispatcher.dispatch(env.from_, acl)
            if handled:
                continue

            # 2) classificação
            kind, payload = router.classify_message(env, acl, self.df_aid)

            # 3) conversas
            if self.conv_mgr:
                self.conv_mgr.on_message(acl)

            # 4) expõe ao iterador
            await self._events.put(event.MsgEvent(env, acl, env.from_, kind, payload))

    # ---------------------- fecho --------------------------------------- #
    async def close(self):
        if self._bg_task:
            self._bg_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._bg_task
        await self.runner.cleanup()
        await self.client.close()


# --------------------------------------------------------------------------- #
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
    """Cria server + client, arranca loop interno e devolve CommEndpoint."""
    from urllib.parse import urlparse

    port = (urlparse(my_aid.addresses[0]).port or 80)
    client = http_client or HttpMtpClient()

    server, runner, site = await start_server(
        on_message=None, bind_host=bind_host, port=port, loop=loop
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

    # ConversationManager (ponto 4)
    async def _low_level_send(msg: AclMessage, url: str | None):
        dst = msg.receivers[0]
        await client.send(dst, my_aid, msg, url or _first_url(dst))

    ep.conv_mgr = ConversationManager(send_fn=_low_level_send)

    # lançar o pump background
    ep._bg_task = asyncio.create_task(ep._pump())

    # auto‑registro DF
    if auto_register:
        if df_aid is None:
            raise ValueError("auto_register=True mas df_aid=None")
        await ep.register_df(
            df_aid,
            services or [],
            df_url=df_aid.addresses[0],
        )

    return ep
