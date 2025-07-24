# MIT License
# Copyright (c) 2025 Santiago Bossa
# See LICENSE file in the project root for full license text.

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

from .message.acl import AclMessage
from .sl_parser import parse
from .sl_visitor import build_ast
from . import sl0


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
