# peak_acl/sl_parser.py
"""
FIPA-SL parser/serialiser baseado no ANTLR 4.

✔️ parse(text)      -> AST Python (ou directamente o objecto que precisares)
✔️ dumps(obj)       -> string SL

Para já devolvemos apenas o parse tree do ANTLR para provar que funciona;
mais tarde podes percorrer com o visitor e construir uma dataclass.
"""

from __future__ import annotations
import io

from antlr4 import InputStream, CommonTokenStream
from .generated.FipaSLLexer  import FipaSLLexer
from .generated.FipaSLParser import FipaSLParser
from .generated.FipaSLVisitor import FipaSLVisitor  # vais usar depois

# --- API pública ---------------------------------------------------------
def parse(text: str):
    """Devolve a parse-tree (prova de conceito)."""
    stream  = InputStream(text)
    lexer   = FipaSLLexer(stream)
    tokens  = CommonTokenStream(lexer)
    parser  = FipaSLParser(tokens)
    tree    = parser.msg()               # regra inicial da gramática
    return tree

def dumps(tree) -> str:                  # placeholder
    raise NotImplementedError("serialiser ainda não implementado")

# opcional: um visitor mínimo que imprime nós
class _DebugVisitor(FipaSLVisitor):
    def visitEveryRule(self, ctx):
        print(type(ctx).__name__, ctx.getText())
        return super().visitEveryRule(ctx)

