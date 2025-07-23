# Generated from grammar/FipaSL.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .FipaSLParser import FipaSLParser
else:
    from FipaSLParser import FipaSLParser

# This class defines a complete generic visitor for a parse tree produced by FipaSLParser.

class FipaSLVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by FipaSLParser#sexpr.
    def visitSexpr(self, ctx:FipaSLParser.SexprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by FipaSLParser#list.
    def visitList(self, ctx:FipaSLParser.ListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by FipaSLParser#elements.
    def visitElements(self, ctx:FipaSLParser.ElementsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by FipaSLParser#stringAtom.
    def visitStringAtom(self, ctx:FipaSLParser.StringAtomContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by FipaSLParser#numberAtom.
    def visitNumberAtom(self, ctx:FipaSLParser.NumberAtomContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by FipaSLParser#symbolAtom.
    def visitSymbolAtom(self, ctx:FipaSLParser.SymbolAtomContext):
        return self.visitChildren(ctx)



del FipaSLParser