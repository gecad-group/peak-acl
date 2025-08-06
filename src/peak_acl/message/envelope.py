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

# src/peak_acl/message/envelope.py
"""
Envelope representation for FIPA-ACL message transport (JADE-compatible).

This module defines :class:`Envelope`, which wraps addressing and transport
metadata required by JADE's HTTP-MTP (and similar) around an ACL payload.
It includes XML (de)serialization helpers to interoperate with JADE/FIPA tools.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import xml.etree.ElementTree as ET

from .aid import AgentIdentifier

# --------------------------------------------------------------------------- #
# JADE date-time format: YYYYMMDDZHHMMSSffffff (microseconds) + literal 'Z'
# JADE effectively uses milliseconds; we trim the last three digits on output.
# --------------------------------------------------------------------------- #
RFC_FMT = "%Y%m%dZ%H%M%S%f"  # JADE uses milliseconds + 'Z'


# --------------------------------------------------------------------------- #
# Envelope
# --------------------------------------------------------------------------- #
@dataclass
class Envelope:
    """Transport envelope for ACL payloads.

    Attributes
    ----------
    to_ :
        Recipient agent identifier.
    from_ :
        Sender agent identifier.
    date :
        UTC timestamp when the envelope was created.
    payload_length :
        Size in bytes of the serialized ACL message (payload).
    acl_rep :
        ACL representation identifier (defaults to ``"fipa.acl.rep.string.std"``).

    Notes
    -----
    * The XML structure generated matches JADE expectations:

      .. code-block:: xml

         <envelope>
           <params index="1">
             <to>...</to>
             <from>...</from>
             <acl-representation>fipa.acl.rep.string.std</acl-representation>
             <payload-length>123</payload-length>
             <date>20250101Z120000123</date>
             <intended-receiver>...</intended-receiver>
           </params>
         </envelope>

    * ``payload_length`` is not recomputed here; caller must supply it.
    """

    to_: AgentIdentifier
    from_: AgentIdentifier
    date: datetime
    payload_length: int
    acl_rep: str = "fipa.acl.rep.string.std"

    # ------------------------------------------------------------------ #
    # XML serialization
    # ------------------------------------------------------------------ #
    def to_xml(self) -> str:
        """Serialize this envelope to an XML string (UTF‑8, with declaration).

        Returns
        -------
        str
            XML string representing the envelope.

        Notes
        -----
        * ``date`` is converted to UTC and formatted with ``RFC_FMT``; the last
          three digits are removed to downscale microseconds to milliseconds,
          mirroring JADE's behavior.
        * ``intended-receiver`` duplicates the ``to`` field per JADE spec.
        """
        env = ET.Element("envelope")
        params = ET.SubElement(env, "params", index="1")

        params.append(self.to_.to_xml_elem("to"))
        params.append(self.from_.to_xml_elem("from"))

        ET.SubElement(params, "acl-representation").text = self.acl_rep
        ET.SubElement(params, "payload-length").text = str(self.payload_length)
        ET.SubElement(params, "date").text = (
            self.date.astimezone(timezone.utc).strftime(RFC_FMT)[:-3]  # trim µs→ms
        )

        # intended-receiver == to
        params.append(self.to_.to_xml_elem("intended-receiver"))

        return ET.tostring(env, encoding="utf-8", xml_declaration=True).decode()

    # ------------------------------------------------------------------ #
    # XML deserialization
    # ------------------------------------------------------------------ #
    @classmethod
    def from_xml(cls, xml: str) -> "Envelope":
        """Parse an :class:`Envelope` from its XML representation.

        Parameters
        ----------
        xml :
            Full XML string containing a single ``<envelope>`` element.

        Returns
        -------
        Envelope
            Parsed envelope instance.

        Raises
        ------
        xml.etree.ElementTree.ParseError
            If the XML string is malformed.
        ValueError
            If date or payload length cannot be parsed.

        Notes
        -----
        Assumes the incoming XML follows the JADE/FIPA schema. Missing tags will
        raise ``AttributeError`` or cause conversions to fail; caller should wrap
        this in higher-level validation if needed.
        """
        root = ET.fromstring(xml)
        params = root.find("./params")
        to_id = AgentIdentifier.from_elem(params.find("to"))
        from_id = AgentIdentifier.from_elem(params.find("from"))
        acl_rep = params.findtext("acl-representation", "")
        payload_length = int(params.findtext("payload-length", "0"))
        date_txt = params.findtext("date", "")
        date = datetime.strptime(date_txt, RFC_FMT).replace(tzinfo=timezone.utc)
        return cls(to_id, from_id, date, payload_length, acl_rep)
