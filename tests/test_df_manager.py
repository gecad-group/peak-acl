import pytest

from peak_acl.message.acl import AclMessage
from peak_acl.message.aid import AgentIdentifier
from peak_acl.runtime import df_manager
from peak_acl.sl import fipa_am, sl0


class DummyClient:
    def __init__(self):
        self.calls = []

    async def send(self, to_ai, from_ai, acl_msg, acc_url):
        self.calls.append((to_ai, from_ai, acl_msg, acc_url))


@pytest.mark.asyncio
async def test_register_deregister_and_search_build_messages():
    my = AgentIdentifier("me", ["http://me/acc"])
    df = AgentIdentifier("df", ["http://df/acc"])
    client = DummyClient()

    reg = await df_manager.register(
        my_aid=my,
        df_aid=df,
        services=[
            ("echo", "tool"),
            fipa_am.ServiceDescription(name="calc", type="math"),
        ],
        languages=["fipa-sl0"],
        http_client=client,
    )
    assert reg.performative == "request"
    assert "register" in reg.content

    der = await df_manager.deregister(my_aid=my, df_aid=df, http_client=client)
    assert "deregister" in der.content

    search = await df_manager.search_services(
        my_aid=my,
        df_aid=df,
        service_name="echo",
        service_type="tool",
        max_results=3,
        http_client=client,
    )
    assert ":max-results 3" in search.content
    assert len(client.calls) == 3
    assert client.calls[0][3] == "http://df/acc"


@pytest.mark.asyncio
async def test_df_helpers_errors_and_custom_url():
    my = AgentIdentifier("me", ["http://me/acc"])
    df_no_addr = AgentIdentifier("df")
    client = DummyClient()

    with pytest.raises(ValueError):
        await df_manager.register(my_aid=my, df_aid=df_no_addr, http_client=client)

    df_with_addr = AgentIdentifier("df", ["http://df/acc"])
    await df_manager.deregister(
        my_aid=my,
        df_aid=df_with_addr,
        http_client=client,
        df_url="http://override/acc",
    )
    assert client.calls[0][3] == "http://override/acc"


@pytest.mark.parametrize(
    "decoded, expected_kind",
    [
        (sl0.Done("ok"), sl0.Done),
        (sl0.Failure("bad"), sl0.Failure),
        ("raw", str),
    ],
)
def test_decode_df_reply_basic(monkeypatch, decoded, expected_kind):
    msg = AclMessage("inform", content="x", language="fipa-sl0")
    monkeypatch.setattr(df_manager, "decode_content", lambda _msg: decoded)

    out = df_manager.decode_df_reply(msg)
    assert isinstance(out, expected_kind)


def test_decode_df_reply_result_and_extract(monkeypatch):
    dfad = sl0.DfAgentDescription(name=AgentIdentifier("a1"), services=[])
    payload = sl0.Result("what", ["set", dfad])
    msg = AclMessage("inform")

    monkeypatch.setattr(df_manager, "decode_content", lambda _msg: payload)
    out = df_manager.decode_df_reply(msg)
    assert len(out) == 1
    assert out[0].name.name == "a1"

    monkeypatch.setattr(df_manager, "decode_content", lambda _msg: payload)
    extracted = df_manager.extract_search_results(msg)
    assert extracted[0].name.name == "a1"


def test_decode_df_reply_list_path_and_failure_helpers(monkeypatch):
    dfad = sl0.DfAgentDescription(name=AgentIdentifier("a2"), services=[])
    msg = AclMessage("inform")
    monkeypatch.setattr(df_manager, "decode_content", lambda _msg: [dfad])
    ads = df_manager.decode_df_reply(msg)
    assert isinstance(ads, sl0.DfAgentDescription)
    assert ads.name.name == "a2"

    monkeypatch.setattr(df_manager, "decode_content", lambda _msg: sl0.Done("ok"))
    assert df_manager.is_df_done_msg(msg) is True

    monkeypatch.setattr(df_manager, "decode_content", lambda _msg: sl0.Failure("no"))
    assert df_manager.is_df_failure_msg(msg) is True


def test_extract_search_results_from_value_with_rebuild_and_unknown():
    aid_expr = [
        "agent-identifier",
        ":name",
        "alice",
        ":addresses",
        ["sequence", "http://alice/acc"],
    ]
    dfad_expr = ["df-agent-description", ":name", aid_expr]

    ads = df_manager.extract_search_results_from_value(["set", dfad_expr, "junk"])
    assert ads is not None
    assert ads[0].name.name == "alice"

    assert df_manager.extract_search_results_from_value("not-a-list") is None
