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
Utilities to build JADE-compatible ``multipart/mixed`` HTTP bodies.

`build_multipart()` serializes an :class:`AclMessage` and wraps it together with
an :class:`Envelope` into a raw multipart payload suitable for the HTTP-MTP
client. It returns the encoded bytes plus the correct ``Content-Type`` header
value (including the generated boundary).
"""

from __future__ import annotations

from typing import Tuple
from datetime import datetime, timezone
import uuid

from ..message.serialize import dumps
from ..message.aid import AgentIdentifier
from ..message.envelope import Envelope
from ..message.acl import AclMessage

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
CRLF = "\r\n"


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def build_multipart(
    to_ai: AgentIdentifier,
    from_ai: AgentIdentifier,
    msg: AclMessage,
) -> Tuple[bytes, str]:
    """Build a JADE-style ``multipart/mixed`` body (bytes) and its Content-Type.

    Parameters
    ----------
    to_ai :
        Recipient agent identifier for the envelope.
    from_ai :
        Sender agent identifier for the envelope.
    msg :
        ACL message to serialize into the second part.

    Returns
    -------
    tuple[bytes, str]
        * body: raw multipart bytes
        * content_type: header value to use (includes boundary param)

    Notes
    -----
    * The envelope is serialized first as ``application/xml``, followed by the
      ACL payload as ``text/plain``.
    * Boundary is generated with a random UUID prefix to minimize collisions.
    """
    acl_str = dumps(msg)
    env_xml = Envelope(
        to_=to_ai,
        from_=from_ai,
        date=datetime.now(timezone.utc),
        payload_length=len(acl_str.encode()),
    ).to_xml()

    boundary = f"BOUNDARY-{uuid.uuid4().hex[:12]}"

    parts = [
        "--" + boundary,
        "Content-Type: application/xml",
        "",
        "",
        env_xml,
        "--" + boundary,
        "Content-Type: text/plain",
        "",
        "",
        acl_str,
        f"--{boundary}--",
        "",
    ]
    body = CRLF.join(parts).encode("utf-8")
    ctype = f'multipart/mixed; boundary="{boundary}"'
    return body, ctype
