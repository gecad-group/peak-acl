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

# src/peak_acl/parse.py
"""
ACL string → :class:`AclMessage` parser using the generated ANTLR4 grammar.

Public API
----------
- :func:`parse`  — parse a raw ACL string into an :class:`AclMessage`.

Raises ``ValueError`` on syntax errors (tokenization or parsing).
"""

from __future__ import annotations

from antlr4 import InputStream, CommonTokenStream

from ..generated.ACLLexer import ACLLexer
from ..generated.ACLParser import ACLParser
from .visitor import MessageBuilder


# --------------------------------------------------------------------------- #
# Public parser
# --------------------------------------------------------------------------- #
def parse(raw: str):
    """Convert a raw ACL string into a fully populated :class:`AclMessage`.

    Parameters
    ----------
    raw :
        ACL text (FIPA/JADE syntax).

    Returns
    -------
    AclMessage
        Parsed message instance.

    Raises
    ------
    ValueError
        If ANTLR reports one or more syntax errors.

    Notes
    -----
    * ``MessageBuilder`` visits the parse tree and constructs the object graph.
    * You can extend ``MessageBuilder`` to decode extra slots or user params.
    """
    stream = InputStream(raw)
    lexer = ACLLexer(stream)
    tokens = CommonTokenStream(lexer)
    parser = ACLParser(tokens)

    tree = parser.message()

    # Optional: check for parser errors (token recognition, etc.)
    if parser.getNumberOfSyntaxErrors() > 0:
        raise ValueError(f"Erro(s) de sintaxe ACL: {parser.getNumberOfSyntaxErrors()}")

    return MessageBuilder(raw).visit(tree)
