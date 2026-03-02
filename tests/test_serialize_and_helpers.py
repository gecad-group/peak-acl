from datetime import datetime

import pytest

from peak_acl.message.acl import AclMessage
from peak_acl.message.aid import AgentIdentifier
from peak_acl.message.serialize import _aid_to_fipa, _content_to_str, _quote_val, dumps
from peak_acl.parser.parse_helpers import to_aid, to_aid_list, to_datetime
from peak_acl.sl import fipa_am, sl0


def _aid_msg(name="alice"):
    return AclMessage(
        "agent-identifier",
        user_params={"name": name, "addresses": ["sequence", f"http://{name}/acc"]},
    )


@pytest.mark.parametrize(
    "value, expected",
    [
        (3, "3"),
        (2.5, "2.5"),
        (True, "True"),
        ('a"b', '"a\\"b"'),
    ],
)
def test_quote_val(value, expected):
    assert _quote_val(value) == expected


def test_content_to_str_and_aid_formatting():
    aid = AgentIdentifier("a", ["http://a/acc"])
    assert "agent-identifier" in _aid_to_fipa(aid)

    assert _content_to_str('"quoted"') == "quoted"
    assert _content_to_str("plain") == "plain"
    assert _content_to_str(77) == "77"

    nested = AclMessage("inform", content="hello")
    assert _content_to_str(nested).startswith("(INFORM")

    assert _content_to_str(sl0.Done("ok")) == "(done ok)"


def test_acl_dumps_all_slots_and_df_patch():
    sender = AgentIdentifier("sender", ["http://sender/acc"])
    recv = AgentIdentifier("recv", ["http://recv/acc"])
    msg = AclMessage(
        "inform",
        sender=sender,
        receivers=[recv],
        reply_to=[recv],
        content="(x)",
        language="fipa-sl0",
        encoding="utf-8",
        ontology="onto",
        protocol="proto",
        conversation_id="cid",
        reply_with="rw",
        in_reply_to="irt",
        reply_by=datetime(2025, 1, 1, 12, 0, 0),
        user_params={"x-num": 3, "x-str": "abc"},
    )
    out = dumps(msg)
    assert out.startswith("(INFORM")
    assert ":sender" in out and ":receiver" in out and ":reply-to" in out
    assert ':content "((x))"' in out
    assert ":reply-by 20250101T120000" in out
    assert ":x-num 3" in out

    msg.content = "((already))"
    out2 = dumps(msg)
    assert ':content "((already))"' in out2


def test_parse_helpers_aid_and_datetime():
    aid = to_aid(_aid_msg("alice"))
    assert aid.name == "alice"

    assert to_aid_list(_aid_msg("single"))[0].name == "single"
    lst = to_aid_list(["set", _aid_msg("a"), _aid_msg("b")])
    assert [x.name for x in lst] == ["a", "b"]

    with pytest.raises(TypeError):
        to_aid("bad")
    with pytest.raises(ValueError):
        to_aid(AclMessage("inform"))
    with pytest.raises(ValueError):
        to_aid(AclMessage("agent-identifier"))
    with pytest.raises(TypeError):
        to_aid_list("bad")

    assert to_datetime(None) is None
    assert to_datetime('"20250715T103845"').year == 2025
    assert to_datetime("20250715Z103845").hour == 10
    assert to_datetime("2025-07-15T10:38:45").minute == 38
    assert to_datetime("20250715").day == 15
    assert to_datetime("not-a-date") is None


def test_fipa_am_conversions_and_rendering():
    aid = AgentIdentifier("agent", ["http://agent/acc"])
    service = fipa_am.ServiceDescription(
        name="echo",
        type="tool",
        properties=[fipa_am.Property("p", "v")],
    )
    ad = fipa_am.build_agent_description(aid=aid, services=[service], ownership=["lab"])
    text = fipa_am.render_register_content(aid, ad)
    assert "register" in text

    sl0_sd = sl0.ServiceDescription(name="echo", type="tool", properties=[("p", "v")])
    out_sd = fipa_am.from_sl0(sl0_sd)
    assert out_sd.properties[0].name == "p"

    sl0_ad = sl0.DfAgentDescription(name=aid, services=[sl0_sd], ownership=["lab"])
    out_ad = fipa_am.from_sl0(sl0_ad)
    assert out_ad.name.name == "agent"

    out_list = fipa_am.from_sl0(sl0.Result("w", [sl0_ad, "junk"]))
    assert len(out_list) == 1
    assert out_list[0].name.name == "agent"

    out_single = fipa_am.from_sl0(sl0.Result("w", sl0_ad))
    assert len(out_single) == 1
    assert fipa_am.from_sl0("raw") == "raw"
