import re
from peak_acl.message.aid import AgentIdentifier
from peak_acl.message.acl import AclMessage
from peak_acl.message.envelope import Envelope
from peak_acl.transport.multipart import build_multipart
from peak_acl.transport.http_mtp import _extract_envelope_acl
from peak_acl.parser import parse


def test_build_multipart_roundtrip():
    to_ai = AgentIdentifier("b", ["http://b"])
    from_ai = AgentIdentifier("a", ["http://a"])
    msg = AclMessage("inform", content="hi")
    body, ctype = build_multipart(to_ai, from_ai, msg)

    m = re.search(r'boundary="?([^";]+)"?', ctype)
    assert m, "missing boundary"
    boundary = m.group(1).encode()

    env_xml, acl_txt = _extract_envelope_acl(body, boundary)
    env = Envelope.from_xml(env_xml)
    acl = parse(acl_txt)

    assert env.to_.name == to_ai.name
    assert acl.content == "hi"
