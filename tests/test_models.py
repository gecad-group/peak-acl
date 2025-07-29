import xml.etree.ElementTree as ET
from datetime import datetime, timezone

from peak_acl.message import AgentIdentifier, Envelope


def test_agent_identifier_xml_roundtrip():
    aid = AgentIdentifier("alice", ["http://localhost/mtp"])
    xml = ET.tostring(aid.to_xml_elem("receiver"), encoding="unicode")
    parsed = AgentIdentifier.from_elem(ET.fromstring(xml))
    assert parsed == aid


def test_envelope_xml_roundtrip():
    to_ai = AgentIdentifier("bob")
    from_ai = AgentIdentifier("alice")
    dt = datetime(2025, 1, 1, 12, 0, 0, 123456, tzinfo=timezone.utc)
    env = Envelope(to_ai, from_ai, dt, payload_length=5)
    xml = env.to_xml()
    parsed = Envelope.from_xml(xml)
    assert parsed.to_ == env.to_
    assert parsed.from_ == env.from_
    assert parsed.payload_length == env.payload_length
    assert parsed.acl_rep == env.acl_rep
    diff = abs((parsed.date - env.date).total_seconds())
    assert diff < 1
