// ======================================================================
//  FIPA-SL  (Specification SC00061G, SC00070J)
//  Grammar ANTLR‑4  •  Output target: Python3
// ======================================================================

grammar FipaSL;

// ─────────────────────────────────────────────
sexpr        : list | atom ;
list         : LPAREN elements? RPAREN ;
elements     : sexpr+ ;

atom         : QUOTE         #stringAtom
             | NUMBER        #numberAtom
             | SYMBOL        #symbolAtom
             ;

// ────── lexer ─────────────────────────────────
LPAREN  : '(' ;
RPAREN  : ')' ;
QUOTE   : '"' ( '\\' . | ~["\\] )* '"' ;
NUMBER  : '-'? [0-9]+ ('.' [0-9]+)? ;
SYMBOL  : [a-zA-Z_][a-zA-Z0-9_\-]* ;

WS      : [ \t\r\n]+          -> skip ;
COMMENT : ';' ~[\r\n]*        -> skip ;