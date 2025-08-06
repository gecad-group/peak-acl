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

# peak_acl/router.py
"""
Utility that classifies inbound messages into a ``(kind, payload)`` tuple,
according to :data:`peak_acl.event.Kind`.

Centralizes logic to:
* Distinguish DF vs. external senders
* Decode SL0 payloads
* Use :func:`df_manager.decode_df_reply` for DF replies
"""

from __future__ import annotations

from typing import Tuple, Any

from .event import Kind
from ..message.envelope import Envelope
from ..message.acl import AclMessage
from ..message.aid import AgentIdentifier
from . import df_manager
from . import content as content_utils
from ..sl import sl0


# --------------------------------------------------------------------------- #
# classify_message
# --------------------------------------------------------------------------- #
def classify_message(
    env: Envelope,
    acl: AclMessage,
    df_aid: AgentIdentifier | None,
) -> Tuple[Kind, Any]:
    """Return ``(kind, payload)`` following the :data:`Kind` table.

    Parameters
    ----------
    env :
        Transport envelope (used to identify sender).
    acl :
        The ACL message itself.
    df_aid :
        Known DF identifier (or ``None`` if unknown). Matching is by ``name``.

    Returns
    -------
    tuple[Kind, Any]
        Classification label plus decoded payload (or raw content fallback).

    Notes
    -----
    * DF detection is name-based only; if multiple DFs or aliases exist, you
      may need a stronger check (e.g. address match).
    * SL0 decoding errors yield ``("ext-raw", "...")`` with a short message.
    """
    sender_is_df = df_aid is not None and env.from_.name == df_aid.name

    # ------------------------------------------------------------------ #
    # Messages coming from the DF
    # ------------------------------------------------------------------ #
    if sender_is_df:
        perf = acl.performative_upper

        if perf == "NOT-UNDERSTOOD":
            return "df-not-understood", acl.get("content", "<sem content>")

        payload = df_manager.decode_df_reply(acl)

        if isinstance(payload, sl0.Done):
            return "df-done", payload

        if isinstance(payload, sl0.Failure):
            return "df-failure", payload

        if isinstance(payload, list):  # list[AgentDescription]
            return "df-result", payload

        # Generic fallback
        return "df", payload

    # ------------------------------------------------------------------ #
    # Messages from other agents
    # ------------------------------------------------------------------ #
    lang = str(acl.get("language", "")).lower()

    if lang == "fipa-sl0":
        try:
            payload = content_utils.decode_content(acl)
            return "ext-sl0", payload
        except Exception as exc:  # invalid payload
            return "ext-raw", f"(SL0 inválido) {exc}: {acl.get('content', '')}"
    else:
        return "ext-raw", acl.get("content", "<sem content>")
