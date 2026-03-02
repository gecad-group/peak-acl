from datetime import datetime

import pytest

from peak_acl.message.acl import AclMessage, _norm_performative
from peak_acl.message.aid import AgentIdentifier


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("inform", "INFORM"),
        ("  query_if  ", "QUERY-IF"),
        ("not-understood", "NOT-UNDERSTOOD"),
    ],
)
def test_norm_performative_and_property(raw, expected):
    assert _norm_performative(raw) == expected
    assert AclMessage(raw).performative_upper == expected


def test_acl_message_dict_like_access_and_mutation():
    msg = AclMessage("inform")
    dt = datetime(2025, 1, 1)

    msg["content"] = "hello"
    msg["language"] = "fipa-sl0"
    msg["encoding"] = "utf-8"
    msg["ontology"] = "fipa-agent-management"
    msg["protocol"] = "fipa-request"
    msg["conversation-id"] = "c1"
    msg["reply-with"] = "rw"
    msg["in-reply-to"] = "irt"
    msg["reply-by"] = dt
    msg["X-Custom"] = 7

    assert msg["content"] == "hello"
    assert msg["language"] == "fipa-sl0"
    assert msg["encoding"] == "utf-8"
    assert msg["ontology"] == "fipa-agent-management"
    assert msg["protocol"] == "fipa-request"
    assert msg["conversationid"] == "c1"
    assert msg["replywith"] == "rw"
    assert msg["inreplyto"] == "irt"
    assert msg["replyby"] == dt
    assert msg["x-custom"] == 7

    assert "protocol" in msg
    assert "x-custom" in msg
    assert "missing" not in msg
    assert msg.get("missing", "fallback") == "fallback"


def test_acl_message_receiver_helpers():
    msg = AclMessage("request")
    alice = AgentIdentifier("alice")
    bob = AgentIdentifier("bob")

    msg.add_receiver(alice)
    msg.add_reply_to(bob)

    assert msg.receivers == [alice]
    assert msg.reply_to == [bob]

    with pytest.raises(KeyError):
        _ = msg["does-not-exist"]
