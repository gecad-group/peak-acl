# peak_acl/content.py
"""
Helpers para decodificar o slot :content conforme a linguagem
indicada na ACL (language=fipa-sl*, …).

Ordem de tentativa:
  1) Grammar completa FIPA‑SL (ANTLR)  → AST (SLSentence, …)
  2) Implementação ad‑hoc SL0         → dataclasses sl0.*
  3) String original (fallback)
"""
from __future__ import annotations
from typing import Any

from .message.acl import AclMessage

from .sl_parser   import parse         
from .sl_visitor  import build_ast     
from . import sl0


# --------------------------------------------------------------------------- #
def decode_content(msg: AclMessage) -> Any:
    """
    Devolve o payload já decodificado:

        • AST FIPA‑SL (objetos do seu visitor)  se language =~ fipa-sl*
        • Objetos sl0.*                         para replies DF/AMS legacy
        • str / bytes / object original         caso não reconheça
    """
    txt = msg.content
    if not (isinstance(txt, str) and
            msg.language and msg.language.lower().startswith("fipa-sl")):
        return txt                    # não é SL → devolve tal‑qual

    clean = txt.strip()
    if not (clean.startswith("(") and clean.endswith(")")):
        return txt                    # formato inesperado

    # 1) grammar completa -------------------------------------------------
    try:
        tree = parse(clean)           # parse‑tree ANTLR
        return build_ast(tree)        # AST rico (SLSentence, …)
    except Exception:
        # 2) compatibilidade SL0 -----------------------------------------
        try:
            return sl0.loads(clean)
        except Exception:
            # 3) fallback bruto ------------------------------------------
            return txt
