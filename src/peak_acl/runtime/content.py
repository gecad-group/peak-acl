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

# peak_acl/content.py
"""
Helpers to decode the ACL ``content`` slot according to the declared language
(e.g., ``language = "fipa-sl..."``).

Decoding order:
  1) Full FIPA-SL grammar (ANTLR)  → rich AST (SLSentence, …)
  2) Ad-hoc SL0 implementation     → ``sl0.*`` dataclasses
  3) Original string/bytes/object  → fallback (no decoding)

Public API
----------
- :func:`decode_content`
"""

from __future__ import annotations

from typing import Any

from ..message.acl import AclMessage
from ..sl.sl_parser import parse
from ..sl.sl_visitor import build_ast
from ..sl import sl0


# --------------------------------------------------------------------------- #
# decode_content
# --------------------------------------------------------------------------- #
def decode_content(msg: AclMessage) -> Any:
    """Return the decoded payload based on the message's ``language`` slot.

    The function inspects ``msg.language`` and, if it starts with ``"fipa-sl"``,
    tries to parse the content as follows:

    1. **Full FIPA-SL via ANTLR** – returns the AST created by ``build_ast``.
    2. **SL0 compatibility layer** – returns objects from ``sl0`` module.
    3. **Fallback** – returns the original ``msg.content`` unchanged.

    Parameters
    ----------
    msg :
        ACL message whose ``content`` and ``language`` fields are inspected.

    Returns
    -------
    Any
        Parsed AST/object or the original content value.

    Notes
    -----
    * Any parsing error is swallowed intentionally; the next strategy is tried.
    * If ``content`` is not a ``str`` or the language is not SL, the original
      value is returned unchanged.
    """
    txt = msg.content
    if not (isinstance(txt, str) and msg.language and msg.language.lower().startswith("fipa-sl")):
        return txt  # Not SL → return as-is

    clean = txt.strip()
    if not (clean.startswith("(") and clean.endswith(")")):
        return txt  # Unexpected format

    # 1) Full grammar (ANTLR) -------------------------------------------- #
    try:
        tree = parse(clean)           # ANTLR parse-tree
        return build_ast(tree)        # Rich AST (SLSentence, …)
    except Exception:
        # 2) SL0 compatibility ------------------------------------------- #
        try:
            return sl0.loads(clean)
        except Exception:
            # 3) Raw fallback -------------------------------------------- #
            return txt
