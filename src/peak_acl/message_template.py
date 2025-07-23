"""
MessageTemplate – filtro simples à la JADE
Permite combinar performative, protocol e ontology.
"""

from __future__ import annotations
from typing import Optional

from .message.acl import AclMessage


class MessageTemplate:
    __slots__ = ("performative", "protocol", "ontology")

    def __init__(
        self,
        *,
        performative: Optional[str] = None,
        protocol: Optional[str] = None,
        ontology: Optional[str] = None,
    ):
        self.performative = performative.upper() if performative else None
        self.protocol = protocol.lower() if protocol else None
        self.ontology = ontology.lower() if ontology else None

    # --------------------------------------------------------------- #
    def match(self, acl: AclMessage) -> bool:
        """True se o ACL coincide com todos os campos definidos no template."""
        if self.performative and acl.performative_upper != self.performative:
            return False
        if self.protocol and (acl.protocol or "").lower() != self.protocol:
            return False
        if self.ontology and (acl.ontology or "").lower() != self.ontology:
            return False
        return True
