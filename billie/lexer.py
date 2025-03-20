from billie.token import Token, TokenType, lookup_ident
from typing import Any, Optional, Dict


class Lexer:
    def __init__(self, source: str) -> None:
        self.source = source

        self.position: int = -1
        self.read_position: int = 0
        self.line_no: int = 1

        self.token_map: Dict[str, TokenType] = {
            '+': TokenType.PLUS,
            '-': TokenType.MINUS,
            '*': TokenType.ASTERISK,
            '/': TokenType.SLASH,
            '%': TokenType.MODULUS,
            '<': TokenType.LT,
            '>': TokenType.GT,
            '=': TokenType.EQ,
            ':': TokenType.COLON,
            ';': TokenType.SEMICOLON,
            ',': TokenType.COMMA,
            '"': TokenType.STRING,
            '(': TokenType.LPAREN,
            ')': TokenType.RPAREN,
            '{': TokenType.LBRACE,
            '}': TokenType.RBRACE,
            '!': TokenType.BANG,
        }

        self.multi_char_tokens = {
            '->': TokenType.ARROW,
            '<=': TokenType.LT_EQ,
            '>=': TokenType.GT_EQ,
            '==': TokenType.EQ_EQ,
            '!=': TokenType.NOT_EQ,
            '+=': TokenType.PLUS_EQ,
            '-=': TokenType.MINUS_EQ,
            '*=': TokenType.MUL_EQ,
            '/=': TokenType.DIV_EQ,
            '++': TokenType.PLUS_PLUS,
            '--': TokenType.MINUS_MINUS,
            '&&': TokenType.AND,
            '||': TokenType.OR
        }

        self.current_char: Optional[str] = None
        self.read_char()

    def read_char(self) -> None:
        """ Reads the next char in the source input file """
        if self.read_position >= len(self.source):
            self.current_char = None
        else:
            self.current_char = self.source[self.read_position]

        self.position = self.read_position
        self.read_position += 1

    def peek_char(self) -> Optional[str]:
        """ Peeks to the upcoming char without advancing the lexer position """
        if self.read_position >= len(self.source):
            return None
        
        return self.source[self.read_position]

    def skip_whitespace(self) -> None:
        while self.current_char in [' ', '\t', '\n', '\r']:
            # Advance the line number if this is a line break
            if self.current_char == '\n':
                self.line_no += 1
            
            self.read_char()

    def skip_comment(self) -> None:
        """ Skips over single-line and multi-line comments """
        if self.current_char == '/' and self.peek_char() == '/':
            while self.current_char is not None and self.current_char != '\n':
                self.read_char()
            self.read_char()
        elif self.current_char == '/' and self.peek_char() == '*':
            self.read_char()  # Consume '*'
            self.read_char()
            while self.current_char is not None:
                if self.current_char == '*' and self.peek_char() == '/':
                    self.read_char()  # Consume '*'
                    self.read_char()  # Consume '/'
                    break
                if self.current_char == '\n':
                    self.line_no += 1
                self.read_char()

    def new_token(self, tt: TokenType, literal: Any) -> Token:
        """ Creates and returns a new token from specified values """
        return Token(type=tt, literal=literal, line_no=self.line_no, position=self.position)
    
    def is_digit(self, ch: str) -> bool:
        """ Checks if the character is a digit """
        return '0' <= ch and ch <= '9'
    
    def is_letter(self, ch: str) -> bool:
        return 'a' <= ch and ch <= 'z' or 'A' <= ch and ch <= 'Z' or ch == '_'
    
    def read_number(self) -> Token:
        """ Reads a number from the input file and returns a Token """
        start_pos: int = self.position
        dot_count: int = 0

        output: str = ""
        while self.is_digit(self.current_char) or self.current_char == '.':
            if self.current_char == '.':
                dot_count += 1

            if dot_count > 1:
                print(f"Too many decimals in number on line {self.line_no}, position {self.position}")
                return self.new_token(TokenType.ILLEGAL, self.source[start_pos:self.position])
            
            output += self.source[self.position]
            self.read_char()

            if self.current_char is None:
                break

        if dot_count == 0:
            return self.new_token(TokenType.INT, int(output))
        else:
            return self.new_token(TokenType.FLOAT, float(output))
    
    def read_identifier(self) -> str:
        position = self.position
        while self.current_char is not None and (self.is_letter(self.current_char) or self.current_char.isalnum()):
            self.read_char()

        return self.source[position:self.position]
    
    def read_string(self) -> str:
        position: int = self.position + 1
        while True:
            self.read_char()
            if self.current_char == '"' or self.current_char is None:
                break
        return self.source[position:self.position]

    def next_token(self) -> list[Token]:
        """ Main function for executing the Lexer """
        while True:
            self.skip_whitespace()
            if self.current_char is None:
                return self.new_token(TokenType.EOF, "")
            
            if self.current_char == '/' and self.peek_char() in ('/', '*'):
                self.skip_comment()
                continue  # Restart the loop to re-skip spaces if needed
            
            # Checking multi-character tokens (==, !=, etc.)
            two_char_seq = self.current_char + (self.peek_char() or "")
            if two_char_seq in self.multi_char_tokens:
                token = self.new_token(self.multi_char_tokens[two_char_seq], two_char_seq)
                self.read_char()  # Read the second character too
                self.read_char()
                return token
            
            # Checking simple tokens
            if self.current_char in self.token_map:
                if self.current_char == '"':
                    token = self.new_token(self.token_map[self.current_char], self.read_string())
                else:
                    token = self.new_token(self.token_map[self.current_char], self.current_char)
                self.read_char()
                return token
            
            if self.is_letter(self.current_char):  # Check identifier
                literal: str = self.read_identifier()
                tt: TokenType = lookup_ident(literal)
                tok = self.new_token(tt=tt, literal=literal)
                return tok

            if self.is_digit(self.current_char):  # Check number
                return self.read_number()
            
            # Unknown token
            token = self.new_token(TokenType.ILLEGAL, self.current_char)
            self.read_char()
            return token
        