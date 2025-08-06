# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2025 Santiago Bossa
#
# This file is part of peak-acl.
#
# peak-acl is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# peak-acl is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with peak-acl.  If not, see the LICENSE file in the project root.

"""
AgentIdentifier model used by FIPA-ACL messages.

This module defines :class:`AgentIdentifier`, a minimal container for an agent's
name and a list of transport addresses (URLs). It also provides XML
serialization/deserialization helpers compatible with the XML structure used
by JADE and common FIPA tools.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List
import xml.etree.ElementTree as ET


# --------------------------------------------------------------------------- #
# AgentIdentifier
# --------------------------------------------------------------------------- #
@dataclass
class AgentIdentifier:
    """Agent identity and transport addresses.

    Attributes
    ----------
    name :
        Logical name or AID of the agent (e.g., ``"agent@platform"``).
    addresses :
        Zero or more transport URLs where this agent can be reached.

    Notes
    -----
    * The XML format produced/consumed follows the pattern:

      .. code-block:: xml

         <tag>
           <agent-identifier>
             <name>agent-name</name>
             <addresses>
               <url>http://...</url>
               ...
             </addresses>
           </agent-identifier>
         </tag>

    * ``xml.etree.ElementTree`` returns ``None`` when a tag has no text; this
      implementation assumes ``<name>`` exists and filters out empty ``<url>``.
    """

    name: str
    addresses: List[str] = field(default_factory=list)

    # ------------------------------------------------------------------ #
    # XML serialization
    # ------------------------------------------------------------------ #
    def to_xml_elem(self, tag: str) -> ET.Element:
        """Serialize this identifier to an XML element.

        Parameters
        ----------
        tag :
            Name of the outer/root tag to use (e.g., ``"receiver"`` or
            ``"reply-to"``).

        Returns
        -------
        xml.etree.ElementTree.Element
            Root element containing the full agent-identifier subtree.

        Examples
        --------
        >>> aid = AgentIdentifier("alice", ["http://host/mtp"])
        >>> elem = aid.to_xml_elem("receiver")
        >>> elem.tag
        'receiver'
        """
        root = ET.Element(tag)
        ai = ET.SubElement(root, "agent-identifier")
        ET.SubElement(ai, "name").text = self.name
        addrs = ET.SubElement(ai, "addresses")
        for url in self.addresses:
            ET.SubElement(addrs, "url").text = url
        return root

    # ------------------------------------------------------------------ #
    # XML deserialization
    # ------------------------------------------------------------------ #
    @classmethod
    def from_elem(cls, elem: ET.Element) -> "AgentIdentifier":
        """Create an :class:`AgentIdentifier` from an XML element.

        Parameters
        ----------
        elem :
            Element whose subtree matches the expected JADE/FIPA structure.

        Returns
        -------
        AgentIdentifier
            Parsed identifier with name and list of URLs.

        Notes
        -----
        If ``<name>`` is missing, the empty string is used.
        Empty or missing ``<url>`` tags are ignored.
        """
        name = elem.findtext("./agent-identifier/name", "")
        urls = [u.text for u in elem.findall(".//url") if u.text]
        return cls(name, urls)
