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

# peak_acl/sl_visitor.py
"""
Visitor that turns the ANTLR FIPA-SL parse tree into a lightweight Python AST
(based on simple dataclasses).

Extend this as you need more FIPA-SL constructs (quantifiers, logic ops, etc.).

Public API
----------
- :func:`build_ast` – convenience wrapper returning an :class:`SLSentence`
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Any

from antlr4.tree.Tree import ParseTree
from ..generated.FipaSLVisitor import FipaSLVisitor
from ..generated.FipaSLParser import FipaSLParser


# --------------------------------------------------------------------------- #
# AST nodes (could be moved to sl_ast.py in the future)
# --------------------------------------------------------------------------- #
@dataclass
class SLString:
    """String literal node (quotes removed)."""
    text: str


@dataclass
class SLNumber:
    """Numeric literal node (stored as float)."""
    value: float


@dataclass
class SLVar:
    """Variable node (e.g., ``?x``)."""
    name: str


@dataclass
class SLFunc:
    """Function application node: ``(name arg1 arg2 ...)``."""
    name: str
    args: List[Any] = field(default_factory=list)  # Any → other AST nodes


@dataclass
class SLAction:
    """``(action actor inner)`` construct."""
    actor: Any  # usually an AgentIdentifier; kept generic
    inner: Any  # inner term/function of the action


@dataclass
class SLSentence:
    """Top-level SL sentence: typically ``(inform ...)`` / ``(request ...)``."""
    performative: str
    slots: List[Any] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# Visitor
# --------------------------------------------------------------------------- #
class ASTBuilder(FipaSLVisitor):
    """
    Visit the parse tree and return an :class:`SLSentence`.

    Supported grammar fragments:
        * msg          → SLSentence
        * performative → initial symbol
        * slot         → ':'NAME term
        * term         → string | number | var | func | action

    The FIPA-SL grammar is recursive; we only implement enough for common
    cases like ``(inform :content "...")`` for now.
    """

    # Entry rule
    def visitMsg(self, ctx: FipaSLParser.MsgContext):
        # ( performative slot* )
        perform = ctx.performative().getText()
        slots = [self.visit(s) for s in ctx.slot()]
        return SLSentence(perform, slots)

    # --- slots ------------------------------------------------------ #
    def visitSlot(self, ctx: FipaSLParser.SlotContext):
        # rule: ':'NAME term
        name = ctx.NAME().getText()
        term = self.visit(ctx.term())
        return (name, term)

    # --- term ------------------------------------------------------- #
    def visitTerm(self, ctx: FipaSLParser.TermContext):
        # Decide which sub-rule matched
        if ctx.stringLiteral():
            return self.visit(ctx.stringLiteral())
        if ctx.numberLiteral():
            return self.visit(ctx.numberLiteral())
        if ctx.variable():
            return self.visit(ctx.variable())
        if ctx.functionExpr():
            return self.visit(ctx.functionExpr())
        if ctx.actionExpr():
            return self.visit(ctx.actionExpr())
        raise ValueError("Unknown term")

    # --- literals --------------------------------------------------- #
    def visitStringLiteral(self, ctx: FipaSLParser.StringLiteralContext):
        txt = ctx.getText()[1:-1]  # strip quotes
        return SLString(txt)

    def visitNumberLiteral(self, ctx: FipaSLParser.NumberLiteralContext):
        return SLNumber(float(ctx.getText()))

    def visitVariable(self, ctx: FipaSLParser.VariableContext):
        return SLVar(ctx.getText())

    # --- function --------------------------------------------------- #
    def visitFunctionExpr(self, ctx: FipaSLParser.FunctionExprContext):
        name = ctx.NAME().getText()
        args = [self.visit(t) for t in ctx.term()]
        return SLFunc(name, args)

    # --- action ----------------------------------------------------- #
    def visitActionExpr(self, ctx: FipaSLParser.ActionExprContext):
        # (action actor inner-term)
        actor = self.visit(ctx.term(0))
        inner = self.visit(ctx.term(1))
        return SLAction(actor, inner)

    # Fallbacks ------------------------------------------------------ #
    def defaultResult(self):
        return None

    def aggregateResult(self, aggregate, nextResult):
        return nextResult if nextResult is not None else aggregate


# --------------------------------------------------------------------------- #
# Convenience helper
# --------------------------------------------------------------------------- #
def build_ast(tree: ParseTree):
    """Shortcut: take a parse tree and return the built AST (:class:`SLSentence`)."""
    visitor = ASTBuilder()
    return visitor.visit(tree)


