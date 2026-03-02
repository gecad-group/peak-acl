import asyncio
from datetime import datetime, timezone

import pytest

from peak_acl.message import AclMessage, AgentIdentifier, Envelope
from peak_acl.runtime import content
from peak_acl.runtime.dispatcher import InboundDispatcher
from peak_acl.runtime.message_template import MessageTemplate
from peak_acl.runtime.router import classify_message
from peak_acl.sl import sl0


def test_decode_content_non_sl_and_bad_format_passthrough():
    raw = "hello"
    non_sl = AclMessage("inform", content=raw, language="plain")
    bad_shape = AclMessage("inform", content="not-parenthesized", language="fipa-sl0")

    assert content.decode_content(non_sl) == raw
    assert content.decode_content(bad_shape) == "not-parenthesized"


def test_decode_content_prefers_full_parser_then_falls_back(monkeypatch):
    msg = AclMessage("inform", content="(ok)", language="fipa-sl0")

    monkeypatch.setattr(content, "parse", lambda txt: {"tree": txt})
    monkeypatch.setattr(content, "build_ast", lambda tree: ("ast", tree["tree"]))
    assert content.decode_content(msg) == ("ast", "(ok)")

    monkeypatch.setattr(content, "parse", lambda _txt: (_ for _ in ()).throw(ValueError("boom")))
    monkeypatch.setattr(content.sl0, "loads", lambda txt: ("sl0", txt))
    assert content.decode_content(msg) == ("sl0", "(ok)")


def test_decode_content_returns_raw_when_all_decoders_fail(monkeypatch):
    msg = AclMessage("inform", content="(x)", language="fipa-sl0")
    monkeypatch.setattr(content, "parse", lambda _txt: (_ for _ in ()).throw(RuntimeError("bad")))
    monkeypatch.setattr(content.sl0, "loads", lambda _txt: (_ for _ in ()).throw(RuntimeError("bad2")))

    assert content.decode_content(msg) == "(x)"


@pytest.mark.asyncio
async def test_inbound_dispatcher_matches_first_rule_and_schedules_callback(monkeypatch):
    dispatcher = InboundDispatcher()
    sender = AgentIdentifier("alice")
    acl = AclMessage("inform", content="hi")

    calls = []

    async def cb(_sender, _acl):
        calls.append((_sender.name, _acl.content))

    scheduled = []

    def fake_create_task(coro):
        scheduled.append(coro)

    monkeypatch.setattr(asyncio, "create_task", fake_create_task)

    dispatcher.add(MessageTemplate(performative="request"), cb)
    dispatcher.add(MessageTemplate(performative="inform"), cb)

    matched = await dispatcher.dispatch(sender, acl)
    assert matched is True
    assert len(scheduled) == 1

    await scheduled[0]
    assert calls == [("alice", "hi")]


@pytest.mark.asyncio
async def test_inbound_dispatcher_returns_false_when_no_rule_matches():
    dispatcher = InboundDispatcher()
    matched = await dispatcher.dispatch(AgentIdentifier("alice"), AclMessage("inform"))
    assert matched is False


def test_classify_message_df_and_external_paths(monkeypatch):
    df = AgentIdentifier("df")
    env_df = Envelope(
        to_=AgentIdentifier("me"),
        from_=AgentIdentifier("df"),
        date=datetime.now(timezone.utc),
        payload_length=0,
    )

    not_understood = AclMessage("not-understood", content="why")
    assert classify_message(env_df, not_understood, df) == ("df-not-understood", "why")

    monkeypatch.setattr("peak_acl.runtime.router.df_manager.decode_df_reply", lambda _acl: sl0.Done("ok"))
    assert classify_message(env_df, AclMessage("inform"), df)[0] == "df-done"

    monkeypatch.setattr("peak_acl.runtime.router.df_manager.decode_df_reply", lambda _acl: sl0.Failure("no"))
    assert classify_message(env_df, AclMessage("failure"), df)[0] == "df-failure"

    monkeypatch.setattr("peak_acl.runtime.router.df_manager.decode_df_reply", lambda _acl: ["ad"])
    assert classify_message(env_df, AclMessage("inform"), df) == ("df-result", ["ad"])

    monkeypatch.setattr("peak_acl.runtime.router.df_manager.decode_df_reply", lambda _acl: {"other": 1})
    assert classify_message(env_df, AclMessage("inform"), df) == ("df", {"other": 1})

    env_ext = Envelope(
        to_=AgentIdentifier("me"),
        from_=AgentIdentifier("bob"),
        date=datetime.now(timezone.utc),
        payload_length=0,
    )
    ext_msg = AclMessage("inform", language="fipa-sl0", content="(payload)")
    monkeypatch.setattr("peak_acl.runtime.router.content_utils.decode_content", lambda _acl: {"parsed": True})
    assert classify_message(env_ext, ext_msg, df) == ("ext-sl0", {"parsed": True})

    def _raise(_acl):
        raise ValueError("bad sl")

    monkeypatch.setattr("peak_acl.runtime.router.content_utils.decode_content", _raise)
    kind, payload = classify_message(env_ext, ext_msg, df)
    assert kind == "ext-raw"
    assert payload.startswith("(SL0 inválido)")

    plain = AclMessage("inform")
    assert classify_message(env_ext, plain, df) == ("ext-raw", None)
