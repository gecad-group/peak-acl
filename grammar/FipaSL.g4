// ======================================================================
//  FIPA-SL  (Specification SC00061G, SC00070J)
//  Grammar ANTLR‑4  •  Output target: Python3
//  Autor: peak-mas PoC
// ======================================================================

grammar FipaSL;

// ────── sintaxe de S‑expressões ────────────────────────────────────────
sexpr        : list | atom ;
list         : LPAREN elements? RPAREN ;
elements     : sexpr+ ;

atom         : QUOTE         #stringAtom
             | NUMBER        #numberAtom
             | SYMBOL        #symbolAtom
             ;

// ────── léxico ─────────────────────────────────────────────────────────
LPAREN  : '(' ;
RPAREN  : ')' ;
QUOTE   : '"' ( '\\' . | ~["\\] )* '"' ;
NUMBER  : '-'? [0-9]+ ('.' [0-9]+)? ;
SYMBOL  : [a-zA-Z_][a-zA-Z0-9_\-]* ;

WS      : [ \t\r\n]+          -> skip ;
COMMENT : ';' ~[\r\n]*        -> skip ;