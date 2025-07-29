from peak_acl import parse, dumps
import pytest

RAW_SIMPLE = (
    '(inform '
    ':sender (agent-identifier :name a) '
    ':receiver (set (agent-identifier :name b)) '
    ':content "hi")'
)

RAW_NESTED = (
    '(proxy '
    ':sender (agent-identifier :name a) '
    ':receiver (set (agent-identifier :name b)) '
    ':content (request :sender (agent-identifier :name a) :content "turn_on"))'
)


@pytest.mark.parametrize("raw", [RAW_SIMPLE, RAW_NESTED])
def test_round_trip(raw):
    msg = parse(raw)
    again = dumps(msg)
    # ensure serialized ACL parses back without errors
    parse(again)


def test_missing_content_raises():
    with pytest.raises(ValueError):
        parse('(inform :sender (agent-identifier :name a))')
