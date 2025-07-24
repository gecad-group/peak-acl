# MIT License
# Copyright (c) 2025 Santiago Bossa
# See LICENSE file in the project root for full license text.

# peak_acl/sl_parser.py
"""
FIPA-SL parser/serializer based on ANTLR 4.

Public API
----------
- :func:`parse`  → returns the ANTLR parse tree (proof of concept)
- :func:`dumps`  → placeholder, not implemented yet

Currently we only expose the raw parse tree; you can later walk it with a
visitor (e.g. :class:`FipaSLVisitor`) to build richer Python objects/dataclasses.
"""

from __future__ import annotations

import io  # kept for future use (streams), currently unused

from antlr4 import InputStream, CommonTokenStream
from .generated.FipaSLLexer import FipaSLLexer
from .generated.FipaSLParser import FipaSLParser
from .generated.FipaSLVisitor import FipaSLVisitor  # to be used later

# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def parse(text: str):
    """Return the ANTLR parse tree for the given SL string.

    Parameters
    ----------
    text :
        FIPA-SL text to parse.

    Returns
    -------
    antlr4.ParserRuleContext
        Root node of the parse tree (``msg`` rule).

    Notes
    -----
    * This is intentionally a thin wrapper; syntax errors will surface via the
      ANTLR error listener (default behavior).
    """
    stream = InputStream(text)
    lexer = FipaSLLexer(stream)
    tokens = CommonTokenStream(lexer)
    parser = FipaSLParser(tokens)
    tree = parser.msg()  # entry rule of the grammar
    return tree


def dumps(tree) -> str:  # placeholder
    """Serialize a parse tree back to SL text (not implemented)."""
    raise NotImplementedError("serializer not implemented yet")


# --------------------------------------------------------------------------- #
# Optional debug visitor
# --------------------------------------------------------------------------- #
class _DebugVisitor(FipaSLVisitor):
    """Minimal visitor that prints every rule; useful for debugging grammars."""

    def visitEveryRule(self, ctx):
        print(type(ctx).__name__, ctx.getText())
        return super().visitEveryRule(ctx)
