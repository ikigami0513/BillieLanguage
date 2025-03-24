from abc import ABC, abstractmethod
from enum import StrEnum


class NodeType(StrEnum):
    Program = "Program"

    # Statements
    ExpressionStatement = "ExpressionStatement"
    LetStatement = "LetStatement"
    ConstStatement = "ConstStatement"
    FunctionStatement = "FunctionStatement"
    BlockStatement = "BlockStatement"
    ReturnStatement = "ReturnStatement"
    AssignStatement = "AssignStatement"
    IfStatement = "IfStatement"
    WhileStatement = "WhileStatement"
    BreakStatement = "BreakStatement"
    ContinueStatement = "ContinueStatement"
    ForStatement = "ForStatement"
    ImportStatement = "ImportStatement"
    ClassFieldStatement = "ClassFieldStatement"
    ClassMethodStatement = "ClassMethodStatement"
    ClassStatement = "ClassStatement"

    # Expressions
    InfixExpression = "InfixExpression"
    CallExpression = "CallExpression"
    PrefixExpression = "PrefixExpression"
    PostfixExpression = "PostfixExpression"

    # Literals
    IntegerLiteral = "IntegerLiteral"
    FloatLiteral = "FloatLiteral"
    IdentifierLiteral = "IdentifierLiteral"
    BooleanLiteral = "BooleanLiteral"
    StringLiteral = "StringLiteral"
    ClassLiteral = "ClassLiteral"

    # Helper
    FunctionParameter = "FunctionParameter"


class Node(ABC):
    def __init__(self, line_no: int) -> None:
        self.line_no = line_no

    @abstractmethod
    def type(self) -> NodeType:
        """ Returns back the NodeType """
        pass

    @abstractmethod
    def json(self) -> dict:
        """ Returns back the JSON representation of this AST node """
        pass


class Statement(Node):
    pass


class Expression(Node):
    pass


class Program(Node):
    """ The root node for the AST"""
    def __init__(self) -> None:
        self.statements: list[Statement] = []

    def type(self) -> NodeType:
        return NodeType.Program
    
    def json(self) -> dict:
        return {
            "type": self.type().value,
            "statements": [{stmt.type().value: stmt.json()} for stmt in self.statements]
        }
    

# region Helpers
class FunctionParameter(Expression):
    def __init__(self, line_no: int, name: str, value_type: str = None) -> None:
        super().__init__(line_no)
        self.name = name
        self.value_type = value_type

    def type(self) -> NodeType:
        return NodeType.FunctionParameter
    
    def json(self) -> dict:
        return {
            "type": self.type().value,
            "name": self.name,
            "value_type": self.value_type
        }
# endregion Helpers
    

# region Statements
class ExpressionStatement(Statement):
    def __init__(self, line_no: int, expr: Expression = None) -> None:
        super().__init__(line_no)
        self.expr = expr

    def type(self) -> NodeType:
        return NodeType.ExpressionStatement
    
    def json(self) -> dict:
        return {
            "type": self.type().value,
            "expr": self.expr.json()
        }
    

class LetStatement(Statement):
    def __init__(self, line_no: int, name: Expression = None, value: Expression = None, value_type: str = None) -> None:
        super().__init__(line_no)
        self.name = name
        self.value = value
        self.value_type = value_type

    def type(self) -> NodeType:
        return NodeType.LetStatement
    
    def json(self) -> dict:
        return {
            "type": self.type().value,
            "name": self.name.json(),
            "value": self.value.json(),
            "value_type": self.value_type
        }
    

class ConstStatement(Statement):
    def __init__(self, line_no: int, name: Expression = None, value: Expression = None, value_type: str = None) -> None:
        super().__init__(line_no)
        self.name = name
        self.value = value
        self.value_type = value_type

    def type(self) -> NodeType:
        return NodeType.ConstStatement
    
    def json(self) -> dict:
        return {
            "type": self.type().value,
            "name": self.name.json(),
            "value": self.value.json(),
            "value_type": self.value_type
        }
    

class BlockStatement(Statement):
    def __init__(self, line_no: int, statements: list[Statement] = None) -> None:
        super().__init__(line_no)
        self.statements = statements if statements is not None else []

    def type(self) -> NodeType:
        return NodeType.BlockStatement
    
    def json(self) -> dict:
        return {
            "type": self.type().value,
            "statements": [stmt.json() for stmt in self.statements]
        }
    

class ReturnStatement(Statement):
    def __init__(self, line_no: int, return_value: Expression = None) -> None:
        super().__init__(line_no)
        self.return_value = return_value

    def type(self) -> NodeType:
        return NodeType.ReturnStatement
    
    def json(self) -> dict:
        return {
            "type": self.type().value,
            "return_value": self.return_value.json()
        }
    

class FunctionStatement(Statement):
    def __init__(self, line_no: int, parameters: list[FunctionParameter] = [], body: BlockStatement = None, name = None, return_type: str = None) -> None:
        super().__init__(line_no)
        self.parameters = parameters
        self.body = body
        self.name = name
        self.return_type = return_type

    def type(self) -> NodeType:
        return NodeType.FunctionStatement
    
    def json(self) -> dict:
        return {
            "type": self.type().value,
            "name": self.name.json(),
            "return_type": self.return_type,
            "parameters": [p.json() for p in self.parameters],
            "body": self.body.json()
        }


class AssignStatement(Statement):
    def __init__(self, line_no: int, ident: Expression = None, operator: str = "", right_value: Expression = None) -> None:
        super().__init__(line_no)
        self.ident = ident
        self.operator = operator
        self.right_value = right_value

    def type(self) -> NodeType:
        return NodeType.AssignStatement

    def json(self) -> dict:
        return {
            "type": self.type().value,
            "ident": self.ident.json(),
            "operator": self.operator,
            "right_value": self.right_value.json()
        }
    

class IfStatement(Statement):
    def __init__(self, line_no: int, condition: Expression = None, consequence: BlockStatement = None, alternative: BlockStatement = None) -> None:
        super().__init__(line_no)
        self.condition = condition
        self.consequence = consequence
        self.alternative = alternative

    def type(self) -> NodeType:
        return NodeType.IfStatement
    
    def json(self) -> dict:
        return {
            "type": self.type().value,
            "condition": self.condition.json(),
            "consequence": self.consequence.json(),
            "alternative": self.alternative.json() if self.alternative is not None else None
        }
    

class WhileStatement(Statement):
    def __init__(self, line_no: int, condition: Expression, body: BlockStatement = None) -> None:
        super().__init__(line_no)
        self.condition = condition
        self.body = body if body is not None else []

    def type(self) -> NodeType:
        return NodeType.WhileStatement
    
    def json(self) -> dict:
        return {
            "type": self.type().value,
            "condition": self.condition.json(),
            "body": self.body.json()
        }
    

class BreakStatement(Statement):
    def __init__(self, line_no: int):
        super().__init__(line_no)

    def type(self) -> NodeType:
        return NodeType.BreakStatement
    
    def json(self) -> dict:
        return {
            "type": self.type().value
        }
    

class ContinueStatement(Statement):
    def __init__(self, line_no: int):
        super().__init__(line_no)

    def type(self) -> NodeType:
        return NodeType.ContinueStatement
    
    def json(self) -> dict:
        return {
            "type": self.type().value
        }
    

class ForStatement(Statement):
    def __init__(self, line_no: int, var_declaration: LetStatement = None, condition: Expression = None, action: AssignStatement = None, body: BlockStatement = None) -> None:
        super().__init__(line_no)
        self.var_declaration = var_declaration
        self.condition = condition
        self.action = action
        self.body = body

    def type(self) -> NodeType:
        return NodeType.ForStatement
    
    def json(self) -> dict:
        return {
            "type": self.type().value,
            "var_declaration": self.var_declaration.json(),
            "condition": self.condition.json(),
            "action": self.action.json(),
            "body": self.body.json()
        }
    

class ImportStatement(Statement):
    def __init__(self, line_no: int, file_path: str) -> None:
        super().__init__(line_no)
        self.file_path = file_path

    def type(self) -> NodeType:
        return NodeType.ImportStatement
    
    def json(self) -> dict:
        return {
            "type": self.type().value,
            "file_path": self.file_path
        }
    

class FieldClassStatement(Statement):
    def __init__(self, line_no: int, name: Expression = None, value_type: str = None, scope: str = None) -> None:
        super().__init__(line_no)
        self.name = name
        self.value_type = value_type
        self.scope = scope

    def type(self) -> NodeType:
        return NodeType.ClassFieldStatement
    
    def json(self) -> dict:
        return {
            "type": self.type().value,
            "name": self.name.json(),
            "value_type": self.value_type,
            "scope": self.scope
        }
    

class MethodClassStatement(Statement):
    def __init__(self, line_no: int, parameters: list[FunctionParameter] = [], body: BlockStatement = None, name = None, return_type: str = None, scope: str = None) -> None:
        super().__init__(line_no)
        self.parameters = parameters
        self.body = body
        self.name = name
        self.return_type = return_type
        self.scope = scope

    def type(self) -> NodeType:
        return NodeType.ClassMethodStatement
    
    def json(self) -> dict:
        return {
            "type": self.type().value,
            "name": self.name.json(),
            "return_type": self.return_type,
            "parameters": [p.json() for p in self.parameters],
            "body": self.body.json(),
            "scope": self.scope
        }

class ClassStatement(Statement):
    def __init__(self, line_no: int, name: Expression = None, fields: list[FieldClassStatement] = None, methods: list[MethodClassStatement] = None) -> None:
        super().__init__(line_no)
        self.name = name
        self.fields = fields if fields is not None else []
        self.methods = methods if methods is not None else []

    def type(self) -> NodeType:
        return NodeType.ClassStatement
    
    def json(self) -> dict:
        return {
            "type": self.type().value,
            "name": self.name.json(),
            "fields": [field.json() for field in self.fields],
            "methods": [method.json() for method in self.methods]
        }
# endregion


# region Expressions
class InfixExpression(Expression):
    def __init__(self, line_no: int, left_node: Expression, operator: str, right_node: Expression = None):
        super().__init__(line_no)
        self.left_node: Expression = left_node
        self.operator: str = operator
        self.right_node: Expression = right_node

    def type(self) -> NodeType:
        return NodeType.InfixExpression
    
    def json(self) -> dict:
        return {
            "type": self.type().value,
            "left_node": self.left_node.json(),
            "operator": self.operator,
            "right_node": self.right_node.json()
        }
    

class CallExpression(Expression):
    def __init__(self, line_no: int, function: Expression = None, arguments: list[Expression] = None) -> None:
        super().__init__(line_no)
        self.function = function  # IdentifierLiteral
        self.arguments = arguments

    def type(self) -> NodeType:
        return NodeType.CallExpression
    
    def json(self) -> dict:
        return {
            "type": self.type().value,
            "function": self.function.json(),
            "arguments": [arg.json() for arg in self.arguments]
        }
    

class PrefixExpression(Expression):
    def __init__(self, line_no: int, operator: str, right_node: Expression = None) -> None:
        super().__init__(line_no)
        self.operator = operator
        self.right_node = right_node

    def type(self) -> NodeType:
        return NodeType.PrefixExpression
    
    def json(self) -> dict:
        return {
            "type": self.type().value,
            "operator": self.operator,
            "right_node": self.right_node.json()
        }
    

class PostfixExpression(Expression):
    def __init__(self, line_no: int, left_node: Expression, operator: str) -> None:
        super().__init__(line_no)
        self.left_node = left_node
        self.operator = operator

    def type(self) -> NodeType:
        return NodeType.PostfixExpression
    
    def json(self) -> dict:
        return {
            "type": self.type().value,
            "left_node": self.left_node.json(),
            "operator": self.operator
        }
# endregion


# region Literals
class IntegerLiteral(Expression):
    def __init__(self, line_no: int, value: int = None) -> None:
        super().__init__(line_no)
        self.value: int = value

    def type(self) -> NodeType:
        return NodeType.IntegerLiteral
    
    def json(self) -> dict:
        return {
            "type": self.type().value,
            "value": self.value
        }
    

class FloatLiteral(Expression):
    def __init__(self, line_no: int, value: float = None) -> None:
        super().__init__(line_no)
        self.value: float = value

    def type(self) -> NodeType:
        return NodeType.FloatLiteral
    
    def json(self) -> dict:
        return {
            "type": self.type().value,
            "value": self.value
        }
    

class IdentifierLiteral(Expression):
    def __init__(self, line_no: int, value: str = None) -> None:
        super().__init__(line_no)
        self.value: str = value

    def type(self) -> NodeType:
        return NodeType.IdentifierLiteral
    
    def json(self) -> dict:
        return {
            "type": self.type().value,
            "value": self.value
        }
    

class BooleanLiteral(Expression):
    def __init__(self, line_no: int, value: bool = None) -> None:
        super().__init__(line_no)
        self.value = value

    def type(self) -> NodeType:
        return NodeType.BooleanLiteral
    
    def json(self) -> dict:
        return {
            "type": self.type().value,
            "value": self.value
        }
    

class StringLiteral(Expression):
    def __init__(self, line_no: int, value: str = None) -> None:
        super().__init__(line_no)
        self.value: str = value

    def type(self) -> NodeType:
        return NodeType.StringLiteral
    
    def json(self) -> dict:
        return {
            "type": self.type().value,
            "value": self.value
        }
# endregion
