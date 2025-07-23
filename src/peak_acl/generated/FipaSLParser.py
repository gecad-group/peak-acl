# Generated from grammar/FipaSL.g4 by ANTLR 4.13.2
# encoding: utf-8
from antlr4 import *
from io import StringIO
import sys
if sys.version_info[1] > 5:
	from typing import TextIO
else:
	from typing.io import TextIO

def serializedATN():
    return [
        4,1,7,29,2,0,7,0,2,1,7,1,2,2,7,2,2,3,7,3,1,0,1,0,3,0,11,8,0,1,1,
        1,1,3,1,15,8,1,1,1,1,1,1,2,4,2,20,8,2,11,2,12,2,21,1,3,1,3,1,3,3,
        3,27,8,3,1,3,0,0,4,0,2,4,6,0,0,29,0,10,1,0,0,0,2,12,1,0,0,0,4,19,
        1,0,0,0,6,26,1,0,0,0,8,11,3,2,1,0,9,11,3,6,3,0,10,8,1,0,0,0,10,9,
        1,0,0,0,11,1,1,0,0,0,12,14,5,1,0,0,13,15,3,4,2,0,14,13,1,0,0,0,14,
        15,1,0,0,0,15,16,1,0,0,0,16,17,5,2,0,0,17,3,1,0,0,0,18,20,3,0,0,
        0,19,18,1,0,0,0,20,21,1,0,0,0,21,19,1,0,0,0,21,22,1,0,0,0,22,5,1,
        0,0,0,23,27,5,3,0,0,24,27,5,4,0,0,25,27,5,5,0,0,26,23,1,0,0,0,26,
        24,1,0,0,0,26,25,1,0,0,0,27,7,1,0,0,0,4,10,14,21,26
    ]

class FipaSLParser ( Parser ):

    grammarFileName = "FipaSL.g4"

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    sharedContextCache = PredictionContextCache()

    literalNames = [ "<INVALID>", "'('", "')'" ]

    symbolicNames = [ "<INVALID>", "LPAREN", "RPAREN", "QUOTE", "NUMBER", 
                      "SYMBOL", "WS", "COMMENT" ]

    RULE_sexpr = 0
    RULE_list = 1
    RULE_elements = 2
    RULE_atom = 3

    ruleNames =  [ "sexpr", "list", "elements", "atom" ]

    EOF = Token.EOF
    LPAREN=1
    RPAREN=2
    QUOTE=3
    NUMBER=4
    SYMBOL=5
    WS=6
    COMMENT=7

    def __init__(self, input:TokenStream, output:TextIO = sys.stdout):
        super().__init__(input, output)
        self.checkVersion("4.13.2")
        self._interp = ParserATNSimulator(self, self.atn, self.decisionsToDFA, self.sharedContextCache)
        self._predicates = None




    class SexprContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def list_(self):
            return self.getTypedRuleContext(FipaSLParser.ListContext,0)


        def atom(self):
            return self.getTypedRuleContext(FipaSLParser.AtomContext,0)


        def getRuleIndex(self):
            return FipaSLParser.RULE_sexpr

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterSexpr" ):
                listener.enterSexpr(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitSexpr" ):
                listener.exitSexpr(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitSexpr" ):
                return visitor.visitSexpr(self)
            else:
                return visitor.visitChildren(self)




    def sexpr(self):

        localctx = FipaSLParser.SexprContext(self, self._ctx, self.state)
        self.enterRule(localctx, 0, self.RULE_sexpr)
        try:
            self.state = 10
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [1]:
                self.enterOuterAlt(localctx, 1)
                self.state = 8
                self.list_()
                pass
            elif token in [3, 4, 5]:
                self.enterOuterAlt(localctx, 2)
                self.state = 9
                self.atom()
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ListContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def LPAREN(self):
            return self.getToken(FipaSLParser.LPAREN, 0)

        def RPAREN(self):
            return self.getToken(FipaSLParser.RPAREN, 0)

        def elements(self):
            return self.getTypedRuleContext(FipaSLParser.ElementsContext,0)


        def getRuleIndex(self):
            return FipaSLParser.RULE_list

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterList" ):
                listener.enterList(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitList" ):
                listener.exitList(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitList" ):
                return visitor.visitList(self)
            else:
                return visitor.visitChildren(self)




    def list_(self):

        localctx = FipaSLParser.ListContext(self, self._ctx, self.state)
        self.enterRule(localctx, 2, self.RULE_list)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 12
            self.match(FipaSLParser.LPAREN)
            self.state = 14
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if (((_la) & ~0x3f) == 0 and ((1 << _la) & 58) != 0):
                self.state = 13
                self.elements()


            self.state = 16
            self.match(FipaSLParser.RPAREN)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ElementsContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def sexpr(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(FipaSLParser.SexprContext)
            else:
                return self.getTypedRuleContext(FipaSLParser.SexprContext,i)


        def getRuleIndex(self):
            return FipaSLParser.RULE_elements

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterElements" ):
                listener.enterElements(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitElements" ):
                listener.exitElements(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitElements" ):
                return visitor.visitElements(self)
            else:
                return visitor.visitChildren(self)




    def elements(self):

        localctx = FipaSLParser.ElementsContext(self, self._ctx, self.state)
        self.enterRule(localctx, 4, self.RULE_elements)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 19 
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while True:
                self.state = 18
                self.sexpr()
                self.state = 21 
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if not ((((_la) & ~0x3f) == 0 and ((1 << _la) & 58) != 0)):
                    break

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class AtomContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return FipaSLParser.RULE_atom

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)



    class StringAtomContext(AtomContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a FipaSLParser.AtomContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def QUOTE(self):
            return self.getToken(FipaSLParser.QUOTE, 0)

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterStringAtom" ):
                listener.enterStringAtom(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitStringAtom" ):
                listener.exitStringAtom(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitStringAtom" ):
                return visitor.visitStringAtom(self)
            else:
                return visitor.visitChildren(self)


    class NumberAtomContext(AtomContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a FipaSLParser.AtomContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def NUMBER(self):
            return self.getToken(FipaSLParser.NUMBER, 0)

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterNumberAtom" ):
                listener.enterNumberAtom(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitNumberAtom" ):
                listener.exitNumberAtom(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitNumberAtom" ):
                return visitor.visitNumberAtom(self)
            else:
                return visitor.visitChildren(self)


    class SymbolAtomContext(AtomContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a FipaSLParser.AtomContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def SYMBOL(self):
            return self.getToken(FipaSLParser.SYMBOL, 0)

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterSymbolAtom" ):
                listener.enterSymbolAtom(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitSymbolAtom" ):
                listener.exitSymbolAtom(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitSymbolAtom" ):
                return visitor.visitSymbolAtom(self)
            else:
                return visitor.visitChildren(self)



    def atom(self):

        localctx = FipaSLParser.AtomContext(self, self._ctx, self.state)
        self.enterRule(localctx, 6, self.RULE_atom)
        try:
            self.state = 26
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [3]:
                localctx = FipaSLParser.StringAtomContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 23
                self.match(FipaSLParser.QUOTE)
                pass
            elif token in [4]:
                localctx = FipaSLParser.NumberAtomContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 24
                self.match(FipaSLParser.NUMBER)
                pass
            elif token in [5]:
                localctx = FipaSLParser.SymbolAtomContext(self, localctx)
                self.enterOuterAlt(localctx, 3)
                self.state = 25
                self.match(FipaSLParser.SYMBOL)
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx





