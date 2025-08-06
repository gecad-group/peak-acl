"""Core FIPA-ACL message models.

This package exposes the in-memory representation of FIPA messages.  It
includes :class:`AclMessage` along with supporting classes such as
:class:`AgentIdentifier` and :class:`Envelope` that are used throughout
the project.
"""

from .acl import AclMessage
from .aid import AgentIdentifier
from .envelope import Envelope

__all__ = ["AclMessage", "AgentIdentifier", "Envelope"]
