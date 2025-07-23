# peak_acl/sl_visitor.py
"""
Visitor que transforma a parse tree ANTLR (FipaSLParser) num
AST em Python (dataclasses simples).

Pode ser extendido à medida que fores precisando de mais
constructos da FIPA‑SL (quantificadores, operadores lógicos, …).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Any

from antlr4.tree.Tree import ParseTree
from .generated.FipaSLVisitor import FipaSLVisitor
from .generated.FipaSLParser  import FipaSLParser


# ------------------------------------------------------------------ #
#  AST  (podes mover para um ficheiro sl_ast.py se preferires)
# ------------------------------------------------------------------ #
@dataclass
class SLString:
    text: str

@dataclass
class SLNumber:
    value: float

@dataclass
class SLVar:
    name: str

@dataclass
class SLFunc:
    name: str
    args: List[Any] = field(default_factory=list)   # Any = outro nó AST

@dataclass
class SLAction:
    actor: Any            # normalmente um AgentIdentifier → mantemos genérico
    inner: Any            # termo/func da acção

@dataclass
class SLSentence:
    """Topo de cada mensagem SL: tipicamente (inform …) / (request …) …"""
    performative: str
    slots: List[Any] = field(default_factory=list)


# ------------------------------------------------------------------ #
#  Visitor
# ------------------------------------------------------------------ #
class ASTBuilder(FipaSLVisitor):
    """
    Visita a árvore e devolve a raiz (SLSentence).

    Regras suportadas:
        msg          → SLSentence
        performative → símbolo inicial
        term         → string | number | var | func | action
    A gramática da FIPA‑SL é recursiva; vamos tratar apenas
    o suficiente para (inform :content "…") etc.
    """

    # regra inicial na gramática
    def visitMsg(self, ctx: FipaSLParser.MsgContext):
        # ( performative slot* )
        perform = ctx.performative().getText()
        slots   = [self.visit(s) for s in ctx.slot()]
        return SLSentence(perform, slots)

    # --- slots ------------------------------------------------------ #
    def visitSlot(self, ctx: FipaSLParser.SlotContext):
        # regra: ':'NAME term
        name = ctx.NAME().getText()
        term = self.visit(ctx.term())
        return (name, term)

    # --- term ------------------------------------------------------- #
    def visitTerm(self, ctx: FipaSLParser.TermContext):
        # escolhe qual sub‑regra foi usada
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
        raise ValueError("term desconhecido")

    # --- literais --------------------------------------------------- #
    def visitStringLiteral(self, ctx: FipaSLParser.StringLiteralContext):
        txt = ctx.getText()[1:-1]   # remove aspas
        return SLString(txt)

    def visitNumberLiteral(self, ctx: FipaSLParser.NumberLiteralContext):
        return SLNumber(float(ctx.getText()))

    def visitVariable(self, ctx: FipaSLParser.VariableContext):
        return SLVar(ctx.getText())

    # --- função ----------------------------------------------------- #
    def visitFunctionExpr(self, ctx: FipaSLParser.FunctionExprContext):
        name = ctx.NAME().getText()
        args = [self.visit(t) for t in ctx.term()]
        return SLFunc(name, args)

    # --- action ----------------------------------------------------- #
    def visitActionExpr(self, ctx: FipaSLParser.ActionExprContext):
        # (action actor inner‑term)
        actor = self.visit(ctx.term(0))
        inner = self.visit(ctx.term(1))
        return SLAction(actor, inner)

    # fallbacks ------------------------------------------------------ #
    def defaultResult(self):
        return None

    def aggregateResult(self, aggregate, nextResult):
        return nextResult if nextResult is not None else aggregate


# ------------------------------------------------------------------ #
#  Helper de conveniência
# ------------------------------------------------------------------ #
def build_ast(tree: ParseTree):
    """Atalho: recebe parse‑tree e devolve AST (SLSentence)."""
    visitor = ASTBuilder()
    return visitor.visit(tree)


# ------------------------------------------------------------------ #
#  Teste rápido (python -m peak_acl.sl_visitor)
# ------------------------------------------------------------------ #
if __name__ == "__main__":
    from .sl_parser import parse          # usa o wrapper que criaste
    sample = '(inform :content "hello world" :sender john)'
    ast = build_ast(parse(sample))
    print(ast)
