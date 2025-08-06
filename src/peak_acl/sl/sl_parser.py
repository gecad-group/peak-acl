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

# peak_acl/sl_parser.py
"""
FIPA-SL parser/serializer based on ANTLR 4.

Public API
----------
- :func:`parse`  → returns the ANTLR parse tree (proof of concept)
- :func:`dumps`  → extremely naive serializer (uses ``getText()`` if present)

Currently we only expose the raw parse tree; you can later walk it with a
visitor (e.g. :class:`FipaSLVisitor`) to build richer Python objects/dataclasses.
"""

from __future__ import annotations

import io  # kept for future use (streams); currently unused

from antlr4 import InputStream, CommonTokenStream
from ..generated.FipaSLLexer import FipaSLLexer
from ..generated.FipaSLParser import FipaSLParser
from ..generated.FipaSLVisitor import FipaSLVisitor  # for downstream visitors


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
    * Thin wrapper: syntax errors are handled by ANTLR's default listeners.
    """
    stream = InputStream(text)
    lexer = FipaSLLexer(stream)
    tokens = CommonTokenStream(lexer)
    parser = FipaSLParser(tokens)
    tree = parser.msg()  # entry rule of the grammar
    return tree


def dumps(tree) -> str:
    """Very naive serializer: delegates to ANTLR's ``getText()`` if available.

    Warning
    -------
    * Whitespace/comments are lost.
    * Only suitable for simple round-trips; not a full pretty-printer.
    """
    return getattr(tree, "getText", lambda: str(tree))()


# --------------------------------------------------------------------------- #
# Optional debug visitor
# --------------------------------------------------------------------------- #
class _DebugVisitor(FipaSLVisitor):
    """Minimal visitor that prints every rule; useful for grammar debugging."""

    def visitEveryRule(self, ctx):
        print(type(ctx).__name__, ctx.getText())
        return super().visitEveryRule(ctx)
