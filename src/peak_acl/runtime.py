# peak_acl/runtime.py
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import (
    Sequence, Tuple, Optional, Iterable, Union,
    AsyncIterator, Callable, Awaitable,
)

import aiohttp.web

from .message.aid import AgentIdentifier
from .message.acl import AclMessage
from .transport.http_mtp import HttpMtpServer, start_server
from .transport.http_client import HttpMtpClient
from . import df_manager, sl0, event, router
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
class CommEndpoint(AsyncIterator[event.MsgEvent]):
    """
    Endpoint = (HTTP-MTP server + HTTP-client + helpers).

    Também fornece:
        • ConversationManager  (ponto 4)
        • InboundDispatcher    (ponto 5)
    """
    # básicos -------------------------------------------------------------
    my_aid:  AgentIdentifier
    inbox:   asyncio.Queue                    # (Envelope, AclMessage)
    client:  HttpMtpClient
    server:  HttpMtpServer
    runner:  aiohttp.web.AppRunner
    site:    aiohttp.web.TCPSite
    df_aid:  Optional[AgentIdentifier] = None

    # add-ons -------------------------------------------------------------
    dispatcher: InboundDispatcher = field(default_factory=InboundDispatcher)
    conv_mgr:   ConversationManager | None   = None       # inicializado em start_endpoint

    # ------------------- DF helpers ---------------------------------- #
    async def register_df(self, df_aid, services, *,
                          df_url=None, languages=(), ontologies=(),
                          protocols=(), ownership=()):
        await df_manager.register(
            my_aid=self.my_aid, df_aid=df_aid, services=services,
            languages=languages, ontologies=ontologies,
            protocols=protocols, ownership=ownership,
            http_client=self.client, df_url=df_url,
        )

    async def search_df(self, *, service_name=None, service_type=None,
                        max_results=None, df_aid=None, df_url=None):
        df_ai = df_aid or self.df_aid
        if df_ai is None:
            raise ValueError("search_df() sem df_aid definido.")
        await df_manager.search_services(
            my_aid=self.my_aid, df_aid=df_ai,
            service_name=service_name, service_type=service_type,
            max_results=max_results,
            http_client=self.client, df_url=df_url,
        )

    async def deregister_df(self, df_aid=None, *, df_url=None):
        df_ai = df_aid or self.df_aid
        if df_ai is None:
            raise ValueError("deregister_df() sem df_aid definido.")
        await df_manager.deregister(
            my_aid=self.my_aid, df_aid=df_ai,
            http_client=self.client, df_url=df_url,
        )

    # ------------------- envio ACL genérico -------------------------- #
    async def send_acl(
        self,
        *,
        to: Union[AgentIdentifier, Iterable[AgentIdentifier]],
        performative: str,
        content=None,
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

        # serializar SL0 se necessário
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

        for r in receivers:
            await self.client.send(r, self.my_aid, msg, _first_url(r))

        return msg

    # ------------------- Conversation sugar (ponto 4) --------------- #
    async def send_request(self, **kw):
        """
        Atalho para ConversationManager.send_request(); devolve future
        que resolve com INFORM/FAILURE.
        """
        if not self.conv_mgr:
            raise RuntimeError("ConversationManager não inicializado.")
        return await self.conv_mgr.send_request(sender=self.my_aid, **kw)

    # ------------------- Dispatcher API (ponto 5) -------------------- #
    def register_handler(
        self,
        *,
        template: MessageTemplate | None = None,
        performative: str | None = None,
        protocol:    str | None = None,
        ontology:    str | None = None,
        cb: Callback,
    ) -> None:
        """
        Regista `cb(sender, acl)` para msgs que casem no template.

        • Podes fornecer `template=` explicitamente **ou**
        • Usar performative / protocol / ontology (será criado internamente).
        """
        if template is None:
            template = MessageTemplate(
                performative=performative,
                protocol=protocol,
                ontology=ontology,
            )
        self.dispatcher.add(template, cb)

    # ------------------- iterator interface ------------------------- #
    def __aiter__(self):
        return self

    async def __anext__(self) -> event.MsgEvent:
        env, acl = await self.inbox.get()

        # 1) tenta Dispatcher (ponto 5)
        if await self.dispatcher.dispatch(env.from_, acl):
            return await self.__anext__()          # já tratado → próxima msg

        # 2) classificação normal
        kind, payload = router.classify_message(env, acl, self.df_aid)

        # 3) update ConversationManager (ponto 4)
        if self.conv_mgr:
            self.conv_mgr.on_message(acl)

        return event.MsgEvent(env, acl, env.from_, kind, payload)

    # ---------------------------------------------------------------- #
    async def close(self):
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
    """Cria server inbound + client outbound + helpers."""
    from urllib.parse import urlparse
    port = urlparse(my_aid.addresses[0]).port or 80

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

    # -------- ConversationManager (ponto 4) ----------
    async def _ll_send(dst: AgentIdentifier, msg: AclMessage):
        await client.send(dst, my_aid, msg, _first_url(dst))

    ep.conv_mgr = ConversationManager(send_fn=_ll_send)

    # -------- registo DF opcional ----------
    if auto_register:
        if df_aid is None:
            raise ValueError("auto_register=True mas df_aid=None")
        await ep.register_df(
            df_aid,
            services or [],
            df_url=df_aid.addresses[0],
        )

    return ep
