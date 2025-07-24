# MIT License
# Copyright (c) 2025 Santiago Bossa
# See LICENSE file in the project root for full license text.

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

from .generated.ACLLexer import ACLLexer
from .generated.ACLParser import ACLParser
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
