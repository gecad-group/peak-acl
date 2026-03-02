import asyncio

import aiohttp
import pytest

from peak_acl.message.acl import AclMessage
from peak_acl.message.aid import AgentIdentifier
from peak_acl.transport.http_client import HttpMtpClient, HttpMtpError


class FakeResponse:
    def __init__(self, status=200, text="ok"):
        self.status = status
        self._text = text

    async def text(self):
        return self._text


class PostCM:
    def __init__(self, value):
        self.value = value

    async def __aenter__(self):
        if isinstance(self.value, Exception):
            raise self.value
        return self.value

    async def __aexit__(self, *_):
        return False


class FakeSession:
    def __init__(self, values):
        self.values = list(values)
        self.calls = []
        self.closed = False

    def post(self, url, data=None, headers=None):
        self.calls.append((url, data, headers))
        return PostCM(self.values.pop(0))

    async def close(self):
        self.closed = True


@pytest.mark.asyncio
async def test_http_client_send_success_and_status_error(monkeypatch):
    to_ai = AgentIdentifier("to", ["http://to/acc"])
    from_ai = AgentIdentifier("from", ["http://from/acc"])
    msg = AclMessage("inform", content="hello")

    session = FakeSession([FakeResponse(200, "ok")])
    client = HttpMtpClient(retries=0, session=session)
    await client.send(to_ai, from_ai, msg, "http://to/acc")
    assert session.calls[0][0] == "http://to/acc"
    assert "Content-Type" in session.calls[0][2]

    bad_session = FakeSession([FakeResponse(500, "boom")])
    bad_client = HttpMtpClient(retries=0, session=bad_session)
    with pytest.raises(HttpMtpError, match="ACC returned 500"):
        await bad_client.send(to_ai, from_ai, msg, "http://to/acc")


@pytest.mark.asyncio
async def test_http_client_retry_and_close(monkeypatch):
    to_ai = AgentIdentifier("to", ["http://to/acc"])
    from_ai = AgentIdentifier("from", ["http://from/acc"])
    msg = AclMessage("inform", content="hello")

    session = FakeSession([aiohttp.ClientError("nope"), FakeResponse(200, "ok")])
    sleeps = []

    async def fake_sleep(d):
        sleeps.append(d)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)
    monkeypatch.setattr("random.uniform", lambda _a, _b: 0.0)

    client = HttpMtpClient(retries=1, backoff_base=0.01, session=session)
    await client.send(to_ai, from_ai, msg, "http://to/acc")
    assert sleeps == [0.01]

    timeout_session = FakeSession([asyncio.TimeoutError("late")])
    timeout_client = HttpMtpClient(retries=0, session=timeout_session)
    with pytest.raises(HttpMtpError, match="Failed after 0 attempts"):
        await timeout_client.send(to_ai, from_ai, msg, "http://to/acc")

    own_session = FakeSession([FakeResponse()])
    closing_client = HttpMtpClient(retries=0, session=own_session)
    closing_client._owns_session = True
    await closing_client.close()
    assert own_session.closed is True


@pytest.mark.asyncio
async def test_http_client_context_manager():
    session = FakeSession([FakeResponse()])
    client = HttpMtpClient(retries=0, session=session)
    client._owns_session = True
    async with client as cm:
        assert cm is client
    assert session.closed is True
