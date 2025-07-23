# Generated from grammar/FipaSL.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .FipaSLParser import FipaSLParser
else:
    from FipaSLParser import FipaSLParser

# This class defines a complete listener for a parse tree produced by FipaSLParser.
class FipaSLListener(ParseTreeListener):

    # Enter a parse tree produced by FipaSLParser#sexpr.
    def enterSexpr(self, ctx:FipaSLParser.SexprContext):
        pass

    # Exit a parse tree produced by FipaSLParser#sexpr.
    def exitSexpr(self, ctx:FipaSLParser.SexprContext):
        pass


    # Enter a parse tree produced by FipaSLParser#list.
    def enterList(self, ctx:FipaSLParser.ListContext):
        pass

    # Exit a parse tree produced by FipaSLParser#list.
    def exitList(self, ctx:FipaSLParser.ListContext):
        pass


    # Enter a parse tree produced by FipaSLParser#elements.
    def enterElements(self, ctx:FipaSLParser.ElementsContext):
        pass

    # Exit a parse tree produced by FipaSLParser#elements.
    def exitElements(self, ctx:FipaSLParser.ElementsContext):
        pass


    # Enter a parse tree produced by FipaSLParser#stringAtom.
    def enterStringAtom(self, ctx:FipaSLParser.StringAtomContext):
        pass

    # Exit a parse tree produced by FipaSLParser#stringAtom.
    def exitStringAtom(self, ctx:FipaSLParser.StringAtomContext):
        pass


    # Enter a parse tree produced by FipaSLParser#numberAtom.
    def enterNumberAtom(self, ctx:FipaSLParser.NumberAtomContext):
        pass

    # Exit a parse tree produced by FipaSLParser#numberAtom.
    def exitNumberAtom(self, ctx:FipaSLParser.NumberAtomContext):
        pass


    # Enter a parse tree produced by FipaSLParser#symbolAtom.
    def enterSymbolAtom(self, ctx:FipaSLParser.SymbolAtomContext):
        pass

    # Exit a parse tree produced by FipaSLParser#symbolAtom.
    def exitSymbolAtom(self, ctx:FipaSLParser.SymbolAtomContext):
        pass



del FipaSLParser