from enum import StrEnum
from typing import Any, Optional


class TokenType(StrEnum):
    # Special Tokens
    EOF = "EOF"
    ILLEGAL = "ILLEGAL"

    # Data Types
    IDENT = "IDENT"
    INT = "INT"
    FLOAT = "FLOAT"
    STRING = "STRING"

    # Arithmetic Symbols
    PLUS = "PLUS"
    MINUS = "MINUS"
    ASTERISK = "ASTERISK"
    SLASH = "SLASH"
    MODULUS = "MODULUS"

    # Assignment Symbols
    EQ = "EQ"
    PLUS_EQ = "PLUS_EQ"
    MINUS_EQ = "MINUS_EQ"
    MUL_EQ = "MUL_EQ"
    DIV_EQ = "DIV_EQ"

    # Comparaison Symbols
    LT = '<'
    GT = '>'
    EQ_EQ = '=='
    NOT_EQ = '!='
    LT_EQ = '<='
    GT_EQ = '>='

    # Logic Symbols
    AND = 'AND'
    OR = 'OR'

    # Symbols
    COLON = "COLON"
    COMMA = "COMMA"
    SEMICOLON = "SEMICOLON"
    ARROW = "ARROW"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    LBRACE = "LBRACE"
    RBRACE = "RBRACE"

    # Prefix Symbols
    BANG = "BANG"

    # Postfix Symbols
    PLUS_PLUS = "PLUS_PLUS"
    MINUS_MINUS = "MINUS_MINUS"

    # Keywords
    LET = "LET"
    CONST = "CONST"
    FUNCTION = "FUNCTION"
    RETURN = "RETURN"
    IF = "IF"
    ELSE = "ELSE"
    TRUE = "TRUE"
    FALSE = "FALSE"
    WHILE = "WHILE"
    BREAK = "BREAK"
    CONTINUE = "CONTINUE"
    FOR = "FOR"
    IMPORT = "IMPORT"

    # Structures Keyword
    PUBLIC = "PUBLIC"
    PROTECTED = "PROTECTED"
    PRIVATE = "PRIVATE"
    CLASS = "CLASS"

    # Typing
    TYPE = "TYPE"


class Token:
    def __init__(self, type: TokenType, literal: Any, line_no: int, position: int) -> None:
        self.type = type
        self.literal = literal
        self.line_no = line_no
        self.position = position

    def __str__(self) -> str:
        return f"Token[{self.type} : {self.literal} : Line {self.line_no} : Position {self.position}]"
    
    def __repr__(self) -> str:
        return str(self)
        

KEYWORDS: dict[str, TokenType] = {
    "let": TokenType.LET,
    "const": TokenType.CONST,
    "function": TokenType.FUNCTION,
    "return": TokenType.RETURN,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "while": TokenType.WHILE,
    "break": TokenType.BREAK,
    "continue": TokenType.CONTINUE,
    "for": TokenType.FOR,
    "import": TokenType.IMPORT,
    "public": TokenType.PUBLIC,
    "protected": TokenType.PROTECTED,
    "private": TokenType.PRIVATE,
    "class": TokenType.CLASS
}

TYPE_KEYWORDS: list[str] = [
    "int", "float",
    "string", "void",
    "bool"
]

def lookup_ident(ident: str) -> TokenType:
    tt: Optional[TokenType] = KEYWORDS.get(ident)
    if tt is not None:
        return tt
    
    if ident in TYPE_KEYWORDS:
        return TokenType.TYPE
    
    return TokenType.IDENT
