import asyncio
import socket

import pytest

from peak_acl.message import AclMessage, AgentIdentifier
from peak_acl.runtime.conversation import ConversationManager
from peak_acl.runtime.message_template import MessageTemplate
from peak_acl.util.net import discover_ip


def test_message_template_match_is_case_insensitive():
    template = MessageTemplate(
        performative="inform", protocol="FIPA-REQUEST", ontology="HeAlTh"
    )
    acl = AclMessage(
        performative="INFORM",
        protocol="fipa-request",
        ontology="health",
        content="ok",
    )

    assert template.match(acl)


def test_message_template_rejects_mismatch():
    template = MessageTemplate(performative="request", protocol="fipa-request")
    acl = AclMessage(performative="inform", protocol="fipa-request", content="nope")

    assert not template.match(acl)


@pytest.mark.asyncio
async def test_conversation_manager_request_agree_inform_flow():
    sent = []

    async def fake_send(msg, url):
        sent.append((msg, url))

    sender = AgentIdentifier("sender@host", ["http://sender/acc"])
    receiver = AgentIdentifier("receiver@host", ["http://receiver/acc"])
    manager = ConversationManager(fake_send)

    fut = await manager.send_request(
        sender=sender,
        receiver=receiver,
        content="(do action)",
        url="http://receiver/acc",
    )

    sent_msg, sent_url = sent[0]
    assert sent_msg.performative_upper == "REQUEST"
    assert sent_url == "http://receiver/acc"

    agree = AclMessage("agree", conversation_id=sent_msg.conversation_id)
    manager.on_message(agree)
    assert not fut.done()

    inform = AclMessage(
        "inform", conversation_id=sent_msg.conversation_id, content="done"
    )
    manager.on_message(inform)
    final = await fut

    assert final.performative_upper == "INFORM"
    assert final.content == "done"


@pytest.mark.asyncio
async def test_conversation_manager_request_refuse_finishes_immediately():
    async def fake_send(_msg, _url):
        return None

    sender = AgentIdentifier("sender@host", ["http://sender/acc"])
    receiver = AgentIdentifier("receiver@host", ["http://receiver/acc"])
    manager = ConversationManager(fake_send)

    fut = await manager.send_request(
        sender=sender, receiver=receiver, content="x", url="http://receiver/acc"
    )
    conv_id = next(iter(manager._convs.keys()))

    refuse = AclMessage("refuse", conversation_id=conv_id, content="cannot")
    manager.on_message(refuse)

    final = await fut
    assert final.performative_upper == "REFUSE"
    assert conv_id not in manager._convs


@pytest.mark.asyncio
async def test_conversation_manager_timeout_sets_exception():
    async def fake_send(_msg, _url):
        return None

    sender = AgentIdentifier("sender@host", ["http://sender/acc"])
    receiver = AgentIdentifier("receiver@host", ["http://receiver/acc"])
    manager = ConversationManager(fake_send)

    fut = await manager.send_request(
        sender=sender,
        receiver=receiver,
        content="x",
        url="http://receiver/acc",
        timeout=0.01,
    )

    with pytest.raises(asyncio.TimeoutError):
        await fut


class _BrokenSocket:
    def connect(self, _target):
        raise OSError("offline")

    def getsockname(self):
        return ("0.0.0.0", 0)

    def close(self):
        return None


def test_discover_ip_falls_back_to_hostname(monkeypatch):
    monkeypatch.setattr(socket, "socket", lambda *_args, **_kwargs: _BrokenSocket())
    monkeypatch.setattr(socket, "gethostname", lambda: "local")
    monkeypatch.setattr(socket, "gethostbyname", lambda _host: "10.1.2.3")

    assert discover_ip() == "10.1.2.3"


def test_discover_ip_falls_back_to_loopback(monkeypatch):
    monkeypatch.setattr(socket, "socket", lambda *_args, **_kwargs: _BrokenSocket())
    monkeypatch.setattr(socket, "gethostname", lambda: "local")

    def _boom(_host):
        raise RuntimeError("resolver down")

    monkeypatch.setattr(socket, "gethostbyname", _boom)

    assert discover_ip() == "127.0.0.1"
