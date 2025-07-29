# MIT License
# Copyright (c) 2025 Santiago Bossa
# See LICENSE file in the project root for full license text.

# src/peak_acl/types.py
"""
Lightweight marker type for strings that must remain quoted during serialization.

``QuotedStr`` subclasses :class:`str` and is used by the serializer to
distinguish values that originally came from an ACL STRING token and therefore
need to keep quotes when emitted by ``dumps()``.
"""


class QuotedStr(str):
    """Marker for values parsed from STRING tokens that should stay quoted."""
    pass
