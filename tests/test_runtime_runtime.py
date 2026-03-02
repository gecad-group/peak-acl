import asyncio
from datetime import datetime, timezone

import pytest

from peak_acl.message.acl import AclMessage
from peak_acl.message.aid import AgentIdentifier
from peak_acl.message.envelope import Envelope
from peak_acl.runtime import event
from peak_acl.runtime.runtime import CommEndpoint, _first_url, start_endpoint
from peak_acl.sl import sl0


class DummyRunner:
    def __init__(self):
        self.cleaned = False

    async def cleanup(self):
        self.cleaned = True


class DummyClient:
    def __init__(self):
        self.sent = []
        self.closed = False

    async def send(self, to_ai, from_ai, msg, url):
        self.sent.append((to_ai, from_ai, msg, url))

    async def close(self):
        self.closed = True


class DummyServer:
    def __init__(self):
        self.inbox = asyncio.Queue()


@pytest.mark.asyncio
async def test_comm_endpoint_send_and_df_helpers(monkeypatch):
    my = AgentIdentifier("me", ["http://me/acc"])
    df = AgentIdentifier("df", ["http://df/acc"])
    other = AgentIdentifier("other", ["http://other/acc"])
    ep = CommEndpoint(
        my, asyncio.Queue(), DummyClient(), DummyServer(), DummyRunner(), object(), df
    )

    rec = {}

    async def _record(kind, **kwargs):
        rec[kind] = kwargs

    monkeypatch.setattr(
        "peak_acl.runtime.runtime.df_manager.register",
        lambda **kw: _record("register", **kw),
    )
    monkeypatch.setattr(
        "peak_acl.runtime.runtime.df_manager.search_services",
        lambda **kw: _record("search", **kw),
    )
    monkeypatch.setattr(
        "peak_acl.runtime.runtime.df_manager.deregister",
        lambda **kw: _record("deregister", **kw),
    )

    await ep.register_df(df, [("s", "t")], languages=("l",))
    await ep.search_df(service_name="svc")
    await ep.deregister_df()
    assert rec["register"]["languages"] == ("l",)
    assert rec["search"]["service_name"] == "svc"
    assert rec["deregister"]["df_aid"].name == "df"

    msg = await ep.send_acl(
        to=[other], performative="inform", content=sl0.Done("ok"), protocol="p"
    )
    assert msg.content == "(done ok)"
    assert ep.client.sent[0][3] == "http://other/acc"


@pytest.mark.asyncio
async def test_comm_endpoint_errors_and_close():
    my = AgentIdentifier("me", ["http://me/acc"])
    runner = DummyRunner()
    client = DummyClient()
    ep = CommEndpoint(
        my, asyncio.Queue(), client, DummyServer(), runner, object(), None
    )

    with pytest.raises(ValueError):
        await ep.send_acl(to=[], performative="inform")
    with pytest.raises(ValueError):
        await ep.search_df()
    with pytest.raises(ValueError):
        await ep.deregister_df()
    with pytest.raises(RuntimeError):
        await ep.send_request(to=AgentIdentifier("x"), content="c")

    task = asyncio.create_task(asyncio.sleep(10))
    ep._bg_task = task
    await ep.close()
    assert task.cancelled()
    assert runner.cleaned is True
    assert client.closed is True


def test_first_url_requires_address():
    with pytest.raises(ValueError):
        _first_url(AgentIdentifier("x"))


@pytest.mark.asyncio
async def test_pump_dispatch_classify_and_iteration(monkeypatch):
    my = AgentIdentifier("me", ["http://me/acc"])
    sender = AgentIdentifier("sender", ["http://sender/acc"])
    env = Envelope(
        to_=my, from_=sender, date=datetime.now(timezone.utc), payload_length=0
    )
    acl = AclMessage("inform", content="hi")

    ep = CommEndpoint(
        my, asyncio.Queue(), DummyClient(), DummyServer(), DummyRunner(), object(), None
    )

    async def dispatch(_s, _m):
        return False

    ep.dispatcher.dispatch = dispatch
    monkeypatch.setattr(
        "peak_acl.runtime.runtime.router.classify_message",
        lambda *_: ("ext-raw", {"x": 1}),
    )

    ep.inbox.put_nowait((env, acl))
    pump_task = asyncio.create_task(ep._pump())
    evt = await asyncio.wait_for(ep.__anext__(), timeout=1)
    assert isinstance(evt, event.MsgEvent)
    assert evt.kind == "ext-raw"
    pump_task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await pump_task


@pytest.mark.asyncio
async def test_start_endpoint_auto_register_and_validation(monkeypatch):
    my = AgentIdentifier("me", ["http://127.0.0.1:8080/acc"])
    df = AgentIdentifier("df", ["http://df/acc"])
    client = DummyClient()
    server = DummyServer()
    runner = DummyRunner()

    async def fake_start_server(**kwargs):
        assert kwargs["port"] == 8080
        return server, runner, object()

    async def fake_register(self, df_aid, services, **kwargs):
        self._registered = (df_aid, list(services), kwargs["df_url"])

    monkeypatch.setattr("peak_acl.runtime.runtime.start_server", fake_start_server)
    monkeypatch.setattr(CommEndpoint, "register_df", fake_register)

    ep = await start_endpoint(
        my_aid=my,
        auto_register=True,
        df_aid=df,
        services=[("svc", "type")],
        http_client=client,
    )
    assert ep._registered[0].name == "df"
    assert ep._registered[2] == "http://df/acc"

    await ep.close()

    with pytest.raises(ValueError):
        await start_endpoint(
            my_aid=my, auto_register=True, df_aid=None, http_client=client
        )
