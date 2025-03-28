from billie.lexer import Lexer
from billie.token import TYPE_KEYWORDS, Token, TokenType
from typing import Callable, Optional
from enum import Enum, auto

from billie.ast import Statement, Expression, Program
from billie.ast import ExpressionStatement, LetStatement, ConstStatement, FunctionStatement, ReturnStatement, BlockStatement
from billie.ast import AssignStatement, IfStatement, WhileStatement, BreakStatement, ContinueStatement, ForStatement, ImportStatement
from billie.ast import FieldClassStatement, MethodClassStatement, ClassStatement
from billie.ast import InfixExpression, CallExpression, PrefixExpression, PostfixExpression
from billie.ast import IntegerLiteral, FloatLiteral, IdentifierLiteral, BooleanLiteral, StringLiteral
from billie.ast import FunctionParameter


# Precedence Types
class PrecedenceType(Enum):
    P_LOWEST = 0
    P_LOGICAL_OR = auto()
    P_LOGICAL_AND = auto()
    P_EQUALS = auto()
    P_LESSGREATER = auto()
    P_SUM = auto()
    P_PRODUCT = auto()
    P_EXPONENT = auto()
    P_PREFIX = auto()
    P_CALL = auto()
    P_INDEX = auto()


# Precedence Mapping
PRECEDENCES: dict[TokenType, int] = {
    TokenType.PLUS: PrecedenceType.P_SUM,
    TokenType.MINUS: PrecedenceType.P_SUM,
    TokenType.SLASH: PrecedenceType.P_PRODUCT,
    TokenType.ASTERISK: PrecedenceType.P_PRODUCT,
    TokenType.MODULUS: PrecedenceType.P_PRODUCT,
    TokenType.EQ_EQ: PrecedenceType.P_EQUALS,
    TokenType.NOT_EQ: PrecedenceType.P_EQUALS,
    TokenType.LT: PrecedenceType.P_LESSGREATER,
    TokenType.GT: PrecedenceType.P_LESSGREATER,
    TokenType.LT_EQ: PrecedenceType.P_LESSGREATER,
    TokenType.GT_EQ: PrecedenceType.P_LESSGREATER,
    TokenType.LPAREN: PrecedenceType.P_CALL,
    TokenType.PLUS_PLUS: PrecedenceType.P_INDEX,
    TokenType.MINUS_MINUS: PrecedenceType.P_INDEX,
    TokenType.AND: PrecedenceType.P_LOGICAL_AND,
    TokenType.OR: PrecedenceType.P_LOGICAL_OR
}


class Parser:
    def __init__(self, lexer: Lexer) -> None:
        self.lexer = lexer

        # Just a list of errors caught during parsing
        self.errors: list[str] = []

        self.current_token: Token = None
        self.peek_token: Token = None
        
        self.prefix_parse_fns: dict[TokenType, Callable] = {
            TokenType.IDENT: self.parse_identifier,
            TokenType.INT: self.parse_int_literal,
            TokenType.FLOAT: self.parse_float_literal,
            TokenType.LPAREN: self.parse_grouped_expression,
            TokenType.IF: self.parse_if_statement,
            TokenType.TRUE: self.parse_boolean,
            TokenType.FALSE: self.parse_boolean,
            TokenType.STRING: self.parse_string_literal,
            TokenType.MINUS: self.parse_prefix_expression,
            TokenType.BANG: self.parse_prefix_expression
        }

        self.infix_parse_fns: dict[TokenType, Callable] = {
            TokenType.PLUS: self.parse_infix_expression,
            TokenType.MINUS: self.parse_infix_expression,
            TokenType.SLASH: self.parse_infix_expression,
            TokenType.ASTERISK: self.parse_infix_expression,
            TokenType.MODULUS: self.parse_infix_expression,
            TokenType.EQ_EQ: self.parse_infix_expression,
            TokenType.NOT_EQ: self.parse_infix_expression,
            TokenType.LT: self.parse_infix_expression,
            TokenType.GT: self.parse_infix_expression,
            TokenType.LT_EQ: self.parse_infix_expression,
            TokenType.GT_EQ: self.parse_infix_expression,
            TokenType.LPAREN: self.parse_call_expression,
            TokenType.PLUS_PLUS: self.parse_postfix_expression,
            TokenType.MINUS_MINUS: self.parse_postfix_expression,
            TokenType.AND: self.parse_infix_expression,
            TokenType.OR: self.parse_infix_expression
        }

        # Populate the current_token and peek_token
        self.next_token()
        self.next_token()

    # region Parser Helpers
    def next_token(self) -> None:
        """ Advances the lexer to retrieve the next token """
        self.current_token = self.peek_token
        self.peek_token = self.lexer.next_token()

    def current_token_is(self, tt: TokenType) -> bool:
        return self.current_token.type == tt

    def peek_token_is(self, tt: TokenType) -> bool:
        """ Peeks one token ahead and checks the type """
        return self.peek_token.type == tt
    
    def peek_token_is_assignement(self) -> bool:
        assignment_operators: list[TokenType] = [
            TokenType.EQ,
            TokenType.PLUS_EQ,
            TokenType.MINUS_EQ,
            TokenType.MUL_EQ,
            TokenType.DIV_EQ
        ]
        return self.peek_token.type in assignment_operators
    
    def peek_token_is_scope(self) -> bool:
        scopes: list[TokenType] = [
            TokenType.PUBLIC,
            TokenType.PROTECTED,
            TokenType.PRIVATE
        ]
        return self.peek_token.type in scopes
    
    def current_token_is_scope(self) -> bool:
        scopes: list[TokenType] = [
            TokenType.PUBLIC,
            TokenType.PROTECTED,
            TokenType.PRIVATE
        ]
        return self.current_token.type in scopes
    
    def expect_peek(self, tt: TokenType) -> bool:
        if self.peek_token_is(tt):
            self.next_token()
            return True
        else:
            self.peek_error(tt)
            return False
        
    def current_precedence(self) -> PrecedenceType:
        prec: Optional[int] = PRECEDENCES.get(self.current_token.type)
        if prec is None:
            return PrecedenceType.P_LOWEST
        return prec
    
    def peek_precedence(self) -> PrecedenceType:
        prec: Optional[int] = PRECEDENCES.get(self.peek_token.type)
        if prec is None:
            return PrecedenceType.P_LOWEST
        return prec
    
    def peek_error(self, tt: TokenType) -> None:
        self.errors.append(f"[line {self.peek_token.line_no}] Expected next token to be {tt}, got {self.peek_token.type} ({self.peek_token.literal}) instead.")

    def no_prefix_parse_fn_error(self, tt: TokenType):
        self.errors.append(f"[line {self.current_token.line_no}] No Prefix Parse Function for {tt} ({self.current_token.literal}) found")

    def parse_program(self) -> Program:
        """ Main execution entry to the Parser """
        program = Program()

        while self.current_token.type != TokenType.EOF:
            stmt = self.parse_statement()
            if stmt is not None:
                program.statements.append(stmt)

            self.next_token()

        return program
    
    # region Statement Methods
    def parse_statement(self) -> Statement:
        if self.current_token.type == TokenType.IDENT and self.peek_token_is_assignement():
            return self.parse_assignment_statement()

        match self.current_token.type:
            case TokenType.LET:
                return self.parse_let_statement()
            case TokenType.CONST:
                return self.parse_const_statement()
            case TokenType.FUNCTION:
                return self.parse_function_statement()
            case TokenType.RETURN:
                return self.parse_return_statement()
            case TokenType.WHILE:
                return self.parse_while_statement()
            case TokenType.BREAK:
                return self.parse_break_statement()
            case TokenType.CONTINUE:
                return self.parse_continue_statement()
            case TokenType.FOR:
                return self.parse_for_statement()
            case TokenType.IMPORT:
                return self.parse_import_statement()
            case TokenType.CLASS:
                return self.parse_class_statement()
            case _:
                return self.parse_expression_statement()
    
    def parse_expression_statement(self) -> ExpressionStatement:
        expr = self.parse_expression(PrecedenceType.P_LOWEST)

        if self.peek_token_is(TokenType.SEMICOLON):
            self.next_token()

        stmt = ExpressionStatement(line_no=self.current_token.line_no, expr=expr)
        return stmt
    
    def parse_let_statement(self) -> LetStatement:
        stmt: LetStatement = LetStatement(line_no=self.current_token.line_no)

        if not self.expect_peek(TokenType.IDENT):
            return None
        
        stmt.name = IdentifierLiteral(line_no=self.current_token.line_no, value=self.current_token.literal)

        if not self.expect_peek(TokenType.COLON):
            return None
        
        if not self.expect_peek(TokenType.TYPE):
            return None
        
        stmt.value_type = self.current_token.literal

        if not self.expect_peek(TokenType.EQ):
            return None
        
        self.next_token()

        stmt.value = self.parse_expression(PrecedenceType.P_LOWEST)

        while not self.current_token_is(TokenType.SEMICOLON) and not self.current_token_is(TokenType.EOF):
            self.next_token()
        
        return stmt
    
    def parse_const_statement(self) -> ConstStatement:
        stmt: ConstStatement = ConstStatement(line_no=self.current_token.line_no)

        if not self.expect_peek(TokenType.IDENT):
            return None
        
        stmt.name = IdentifierLiteral(line_no=self.current_token.line_no, value=self.current_token.literal)

        if not self.expect_peek(TokenType.COLON):
            return None
        
        if not self.expect_peek(TokenType.TYPE):
            return None
        
        stmt.value_type = self.current_token.literal

        if not self.expect_peek(TokenType.EQ):
            return None
        
        self.next_token()

        stmt.value = self.parse_expression(PrecedenceType.P_LOWEST)

        while not self.current_token_is(TokenType.SEMICOLON) and not self.current_token_is(TokenType.EOF):
            self.next_token()

        return stmt
    
    def parse_function_statement(self) -> FunctionStatement:
        stmt = FunctionStatement(line_no=self.current_token.line_no)

        if not self.expect_peek(TokenType.IDENT):
            return None
        
        stmt.name = IdentifierLiteral(line_no=self.current_token.line_no, value=self.current_token.literal)

        if not self.expect_peek(TokenType.LPAREN):
            return None
        
        stmt.parameters = self.parse_function_parameters()
        
        if not self.expect_peek(TokenType.ARROW):
            return None
        
        self.next_token()

        stmt.return_type = self.current_token.literal
        if not self.expect_peek(TokenType.LBRACE):
            return None
        
        stmt.body = self.parse_block_statement()
        return stmt
    
    def parse_function_parameters(self) -> list[FunctionParameter]:
        params: list[FunctionParameter] = []

        if self.peek_token_is(TokenType.RPAREN):
            self.next_token()
            return params
        
        self.next_token()

        first_param = FunctionParameter(line_no=self.current_token.line_no, name=self.current_token.literal)

        if not self.expect_peek(TokenType.COLON):
            return None
        
        self.next_token()

        first_param.value_type = self.current_token.literal
        params.append(first_param)

        while self.peek_token_is(TokenType.COMMA):
            self.next_token()
            self.next_token()

            param = FunctionParameter(line_no=self.current_token.line_no, name=self.current_token.literal)

            if not self.expect_peek(TokenType.COLON):
                return None
            
            self.next_token()

            param.value_type = self.current_token.literal
            params.append(param)

        if not self.expect_peek(TokenType.RPAREN):
            return None
        
        return params

    def parse_block_statement(self) -> BlockStatement:
        block_stmt = BlockStatement(line_no=self.current_token.line_no)
        self.next_token()

        while not self.current_token_is(TokenType.RBRACE) and not self.current_token_is(TokenType.EOF):
            stmt: Statement = self.parse_statement()
            if stmt is not None:
                block_stmt.statements.append(stmt)
            self.next_token()
        return block_stmt

    def parse_return_statement(self) -> ReturnStatement:
        stmt = ReturnStatement(line_no=self.current_token.line_no)
        self.next_token()
        stmt.return_value = self.parse_expression(PrecedenceType.P_LOWEST)

        if not self.expect_peek(TokenType.SEMICOLON):
            return None
        return stmt
    
    def parse_assignment_statement(self) -> AssignStatement:
        stmt = AssignStatement(line_no=self.current_token.line_no)

        stmt.ident = IdentifierLiteral(line_no=self.current_token.line_no, value=self.current_token.literal)

        self.next_token()  # Skips the 'IDENT'

        stmt.operator = self.current_token.literal
        self.next_token()  # Skips the operator

        stmt.right_value = self.parse_expression(PrecedenceType.P_LOWEST)

        self.next_token()

        return stmt
    
    def parse_if_statement(self) -> IfStatement:
        condition: Expression = None
        consequence: BlockStatement = None
        alternative: BlockStatement = None

        self.next_token()

        condition = self.parse_expression(PrecedenceType.P_LOWEST)

        if not self.expect_peek(TokenType.LBRACE):
            return None

        consequence = self.parse_block_statement()

        if self.peek_token_is(TokenType.ELSE):
            self.next_token()

            if not self.expect_peek(TokenType.LBRACE):
                return None

            alternative = self.parse_block_statement()

        return IfStatement(line_no=self.current_token.line_no, condition=condition, consequence=consequence, alternative=alternative)
    
    def parse_while_statement(self) -> WhileStatement:
        condition: Expression = None
        body: BlockStatement = None

        self.next_token()  # Skip WHILE

        condition = self.parse_expression(PrecedenceType.P_LOWEST)

        if not self.expect_peek(TokenType.LBRACE):
            return None
        
        body = self.parse_block_statement()

        return WhileStatement(line_no=self.current_token.line_no, condition=condition, body=body)
    
    def parse_break_statement(self) -> BreakStatement:
        self.next_token()
        return BreakStatement(line_no=self.current_token.line_no)
    
    def parse_continue_statement(self) -> ContinueStatement:
        self.next_token()
        return ContinueStatement(line_no=self.current_token.line_no)
    
    def parse_for_statement(self) -> ForStatement:
        stmt: ForStatement = ForStatement(line_no=self.current_token.line_no)

        if not self.expect_peek(TokenType.LPAREN):
            return None
        
        if not self.expect_peek(TokenType.LET):
            return None

        stmt.var_declaration = self.parse_let_statement()

        self.next_token()  # Skip ;

        stmt.condition = self.parse_expression(PrecedenceType.P_LOWEST)

        if not self.expect_peek(TokenType.SEMICOLON):
            return None
        
        self.next_token() # Skip ;

        if self.peek_token_is_assignement():
            # i += 1 or i = i + 1
            stmt.action = self.parse_assignment_statement()
        else:
            # i++
            stmt.action = self.parse_expression(PrecedenceType.P_LOWEST)
        
            self.next_token()

        if not self.expect_peek(TokenType.LBRACE):
            return None
        
        stmt.body = self.parse_block_statement()

        return stmt
    
    def parse_import_statement(self) -> ImportStatement:
        if not self.expect_peek(TokenType.STRING):
            return None
        
        stmt = ImportStatement(line_no=self.current_token.line_no, file_path=self.current_token.literal)

        if not self.expect_peek(TokenType.SEMICOLON):
            return None
        
        return stmt
    
    def parse_class_statement(self) -> ClassStatement:
        stmt = ClassStatement(self.current_token.line_no)

        self.next_token()  # Skips 'class' keyword

        stmt.name = IdentifierLiteral(line_no=self.current_token.line_no, value=self.current_token.literal)
        if not self.expect_peek(TokenType.LBRACE):
            return None

        self.next_token()  # Skips '{'

        while not self.current_token_is(TokenType.RBRACE):  # Loop until closing brace
            if not self.current_token_is_scope():
                return None # Or raise an exception, depending on desired error handling.

            if self.peek_token_is(TokenType.IDENT):
                field = self.parse_class_field()  # Delegate field parsing to a separate function
                if field is None:
                    return None  # Error in field parsing
                stmt.fields.append(field)

                if self.current_token_is(TokenType.SEMICOLON):
                    self.next_token() # Skip semicolon

            elif self.peek_token_is(TokenType.FUNCTION):
                method = self.parse_class_method()
                if method is None:
                    return None
                stmt.methods.append(method)

        TYPE_KEYWORDS.append(stmt.name.value)
        return stmt

    def parse_class_field(self) -> FieldClassStatement:
        field = FieldClassStatement(self.current_token.line_no)
        field.scope = self.current_token.literal

        if not self.expect_peek(TokenType.IDENT):
            return None
        field.name = IdentifierLiteral(line_no=self.current_token.line_no, value=self.current_token.literal)

        if not self.expect_peek(TokenType.COLON):
            return None

        if not self.expect_peek(TokenType.TYPE):
            return None
        field.value_type = self.current_token.literal
        self.next_token() # Consume the type
        return field
    
    def parse_class_method(self) -> MethodClassStatement:
        method = MethodClassStatement(self.current_token.line_no)
        method.scope = self.current_token.literal

        if not self.expect_peek(TokenType.FUNCTION):
            return None
        
        if not self.expect_peek(TokenType.IDENT):
            return None
        
        method.name = IdentifierLiteral(line_no=self.current_token.line_no, value=self.current_token.literal)

        if not self.expect_peek(TokenType.LPAREN):
            return None

        method.parameters = self.parse_function_parameters()

        if not self.expect_peek(TokenType.ARROW):
            return None
        
        self.next_token()

        method.return_type = self.current_token.literal

        if not self.expect_peek(TokenType.LBRACE):
            return None
        
        method.body = self.parse_block_statement()

        self.next_token()

        return method
    #endregion

    # region Expression Methods
    def parse_expression(self, precedence: PrecedenceType) -> Expression:
        prefix_fn: Optional[Callable] = self.prefix_parse_fns.get(self.current_token.type)
        if prefix_fn is None:
            self.no_prefix_parse_fn_error(self.current_token.type)
            return None
        
        left_expr: Expression = prefix_fn()
        if self.current_token.type == TokenType.TYPE and self.current_token.literal in TYPE_KEYWORDS:
            return left_expr

        while not self.peek_token_is(TokenType.SEMICOLON) and precedence.value < self.peek_precedence().value:
            infix_fn: Optional[Callable] = self.infix_parse_fns.get(self.peek_token.type)
            if infix_fn is None:
                return left_expr
            
            self.next_token()

            left_expr = infix_fn(left_expr)
        return left_expr
    
    def parse_infix_expression(self, left_node: Expression) -> Expression:
        """ Parses and returns a normal InfixExpression """
        infix_expr = InfixExpression(line_no=self.current_token.line_no, left_node=left_node, operator=self.current_token.literal)
        precedence = self.current_precedence()
        self.next_token()
        infix_expr.right_node = self.parse_expression(precedence)
        return infix_expr
    
    def parse_grouped_expression(self) -> Expression:
        self.next_token()
        expr: Expression = self.parse_expression(PrecedenceType.P_LOWEST)

        if not self.expect_peek(TokenType.RPAREN):
            return None
        return expr
    
    def parse_call_expression(self, function: Expression) -> CallExpression:
        expr = CallExpression(line_no=self.current_token.line_no, function=function)
        expr.arguments = self.parse_expression_list(TokenType.RPAREN)
        
        return expr
    
    def parse_expression_list(self, end: TokenType) -> list[Expression]:
        e_list: list[Expression] = []

        if self.peek_token_is(end):
            self.next_token()
            return e_list
        
        self.next_token()

        e_list.append(self.parse_expression(PrecedenceType.P_LOWEST))

        while self.peek_token_is(TokenType.COMMA):
            self.next_token()
            self.next_token()

            e_list.append(self.parse_expression(PrecedenceType.P_LOWEST))

        if not self.expect_peek(end):
            return None
        
        return e_list
    
    def parse_prefix_expression(self) -> PrefixExpression:
        prefix_expr = PrefixExpression(line_no=self.current_token.line_no, operator=self.current_token.literal)
        self.next_token()
        prefix_expr.right_node = self.parse_expression(PrecedenceType.P_PREFIX)
        return prefix_expr
    
    def parse_postfix_expression(self, left_node: Expression) -> PostfixExpression:
        return PostfixExpression(line_no=self.current_token.line_no, left_node=left_node, operator=self.current_token.literal)
    # endregion

    # region Prefix Methods
    def parse_identifier(self) -> IdentifierLiteral:
        return IdentifierLiteral(line_no=self.current_token.line_no, value=self.current_token.literal)

    def parse_int_literal(self) -> Expression:
        """ Parses an IntegerLiteral Node from the current token """
        int_lit = IntegerLiteral(line_no=self.current_token.line_no)

        try:
            int_lit.value = int(self.current_token.literal)
        except:
            self.errors.append(f"[line {self.current_token.line_no}] Could not parse `{self.current_token.literal}` as an integer.")
            return None
        
        return int_lit
    
    def parse_float_literal(self) -> Expression:
        """ Parses an FloatLiteral Node from the current token """
        float_lit = FloatLiteral(line_no=self.current_token.line_no)

        try:
            float_lit.value = float(self.current_token.literal)
        except:
            self.errors.append(f"[line {self.current_token.line_no}] Could not parse `{self.current_token.literal}` as n float.")
            return None
        
        return float_lit
    
    def parse_boolean(self) -> BooleanLiteral:
        return BooleanLiteral(line_no=self.current_token.line_no, value=self.current_token_is(TokenType.TRUE))
    
    def parse_string_literal(self) -> StringLiteral:
        return StringLiteral(line_no=self.current_token.line_no, value=self.current_token.literal)
    # endregion
