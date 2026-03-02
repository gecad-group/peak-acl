import pytest

from peak_acl.message.aid import AgentIdentifier
from peak_acl.sl import sl0


def test_sl0_render_variants_and_extractors():
    me = AgentIdentifier("me", ["http://me/acc"])
    sd = sl0.ServiceDescription(
        name="echo",
        type="tool",
        languages=["fipa-sl0"],
        ontologies=["onto"],
        protocols=["fipa-request"],
        properties=[("p", "v")],
    )
    dfad = sl0.DfAgentDescription(
        name=me,
        services=[sd],
        languages=["fipa-sl0"],
        ontologies=["onto"],
        protocols=["fipa-request"],
        ownership=["lab"],
    )

    payloads = [
        sl0.Action(actor=me, act=sl0.Register(dfad)),
        sl0.Action(actor=me, act=sl0.Deregister(dfad)),
        sl0.Action(actor=me, act=sl0.Modify(dfad)),
        sl0.Action(actor=me, act=sl0.Search(template=dfad, max_results=10)),
        sl0.Done("ok"),
        sl0.Failure("err"),
        sl0.Result("what", "value"),
        dfad,
        sd,
        me,
    ]

    for item in payloads:
        text = sl0.dumps(item)
        assert text.startswith("(")

    assert sl0.dumps(123) == "123"

    assert sl0._extract_sequence(["sequence", "a", "b"]) == ["a", "b"]
    assert sl0._extract_sequence(["a", "b"]) == ["a", "b"]
    assert sl0._extract_sequence("a") == ["a"]

    assert sl0._extract_set(["set", "x", "y"]) == ["x", "y"]
    assert sl0._extract_set(["x"]) == ["x"]
    assert sl0._extract_set("x") == ["x"]


@pytest.mark.parametrize(
    "expr, expected_type",
    [
        ("(register (df-agent-description))", sl0.Register),
        ("(deregister (df-agent-description))", sl0.Deregister),
        ("(modify (df-agent-description))", sl0.Modify),
        ("(done anything)", sl0.Done),
        ("(failure reason)", sl0.Failure),
        ("(result what value)", sl0.Result),
        ("(service-description :name n :type t)", sl0.ServiceDescription),
        (
            "(agent-identifier :name a :addresses (sequence http://a/acc))",
            AgentIdentifier,
        ),
    ],
)
def test_sl0_loads_core_forms(expr, expected_type):
    parsed = sl0.loads(expr)
    assert isinstance(parsed, expected_type)


def test_sl0_build_ast_fallback_and_errors():
    generic = sl0.build_ast(["unknown", "x", ["y"]])
    assert generic == ["unknown", "x", ["y"]]

    with pytest.raises(ValueError, match="sem :name"):
        sl0._build_aid(["agent-identifier", ":addresses", ["sequence", "u"]])

    with pytest.raises(ValueError, match="malformado"):
        sl0._build_dfad("bad")


def test_sl0_extract_properties_and_services():
    props = sl0._extract_properties(
        [
            "set",
            ["property", ":name", "n1", ":value", "v1"],
            ["property", ":name", "n2", ":value", "v2"],
        ]
    )
    assert props == [("n1", "v1"), ("n2", "v2")]

    services = sl0._extract_services(
        [
            "set",
            ["service-description", ":name", "svc", ":type", "kind"],
        ]
    )
    assert services[0].name == "svc"
    assert services[0].type == "kind"
