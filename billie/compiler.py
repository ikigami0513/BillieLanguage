from llvmlite import ir
import os
import sys
from typing import Any, Optional

from billie.ast import Node, NodeType, Program, Expression
from billie.ast import ExpressionStatement, LetStatement, ConstStatement, FunctionStatement, ReturnStatement, BlockStatement
from billie.ast import AssignStatement, IfStatement, WhileStatement, ContinueStatement, BreakStatement, ForStatement, ImportStatement
from billie.ast import MethodClassStatement, ClassStatement
from billie.ast import InfixExpression, CallExpression, PrefixExpression, PostfixExpression
from billie.ast import IntegerLiteral, FloatLiteral, IdentifierLiteral, BooleanLiteral, StringLiteral
from billie.ast import FunctionParameter

from billie.environment import Environment

from billie.lexer import Lexer
from billie.parser import Parser

from billie import settings


class Compiler:
    def __init__(self) -> None:
        self.type_map: dict[str, ir.Type] = {
            'int': ir.IntType(64),
            'float': ir.FloatType(),
            'bool': ir.IntType(1),
            'void': ir.VoidType(),
            'string': ir.PointerType(ir.IntType(8))
        }

        self.declared_classes: dict[str, Any] = {}

        # Initialize the main module
        self.module = ir.Module('main')

        # Current builder
        self.builder = ir.IRBuilder()

        # Counter for unique block names
        self.counter = 0

        # Environment reference for the currently compiling scope
        self.env = Environment()

        # Temporary keeping track of errors
        self.errors: list[str] = []

        # Initialize Builtin functions and values
        self.initialize_builtins()

        # Keeps a refenrence to the compiling loop blocks
        self.breakpoints: list[ir.Block] = []
        self.continues: list[ir.Block] = []

        # Keeps a reference to parsed pallets
        self.global_parsed_pallets: dict[str, Program] = {}

        self.is_let = False
        self.let_node: Optional[LetStatement] = None

    def initialize_builtins(self):
        def init_print() -> ir.Function:
            fnty: ir.FunctionType = ir.FunctionType(
                self.type_map['int'],
                [ir.IntType(8).as_pointer()],
                var_arg=True
            )
            return ir.Function(self.module, fnty, 'printf')

        def init_booleans() -> tuple[ir.GlobalVariable, ir.GlobalVariable]:
            bool_type: ir.Type = self.type_map['bool']

            true_var = ir.GlobalVariable(self.module, bool_type, 'true')
            true_var.initializer = ir.Constant(bool_type, 1)
            true_var.global_constant = True

            false_var = ir.GlobalVariable(self.module, bool_type, 'false')
            false_var.initializer = ir.Constant(bool_type, 0)
            false_var.global_constant = True

            return true_var, false_var
        
        self.env.define('print', init_print(), ir.IntType(32))
        
        true_var, false_var = init_booleans()
        self.env.define('true', true_var, true_var.type)
        self.env.define('false', false_var, false_var.type)

    def increment_counter(self) -> int:
        self.counter += 1
        return self.counter

    def compile(self, node: Node) -> None:
        """ Main Recursive loop for compiling the AST """
        match node.type():
            case NodeType.Program:
                self.visit_program(node)
            
            # Statements
            case NodeType.ExpressionStatement:
                self.visit_expression_statement(node)
            case NodeType.LetStatement:
                self.visit_let_statement(node)
            case NodeType.ConstStatement:
                self.visit_const_statement(node)
            case NodeType.FunctionStatement:
                self.visit_function_statement(node)
            case NodeType.BlockStatement:
                self.visit_block_statement(node)
            case NodeType.ReturnStatement:
                return self.visit_return_statement(node)
            case NodeType.AssignStatement:
                return self.visit_assign_statement(node)
            case NodeType.IfStatement:
                self.visit_if_statement(node)
            case NodeType.WhileStatement:
                self.visit_while_statement(node)
            case NodeType.BreakStatement:
                self.visit_break_statement(node)
            case NodeType.ContinueStatement:
                self.visit_continue_statement(node)
            case NodeType.ForStatement:
                self.visit_for_statement(node)
            case NodeType.ImportStatement:
                self.visit_import_statement(node)
            case NodeType.ClassStatement:
                self.visit_class_statement(node)

            # Expressions
            case NodeType.InfixExpression:
                self.visit_infix_expression(node)
            case NodeType.CallExpression:
                self.visit_call_expression(node)
            case NodeType.PostfixExpression:
                self.visit_postfix_expression(node)

    # region Visit Methods
    def visit_program(self, node: Program) -> None:
        # Compile the body
        for stmt in node.statements:
            self.compile(stmt)
    # endregion Visit Methods

    # region Visit Statements Methods
    def visit_expression_statement(self, node: ExpressionStatement) -> None:
        self.compile(node.expr)

    def visit_let_statement(self, node: LetStatement) -> None:
        self.is_let = True
        self.let_node = node
        name: str = node.name.value
        value: Expression = node.value
        value_, Type = self.resolve_value(node=value)

        if self.env.lookup(name) is None:
            # Define and allocate the variable
            if node.value_type in self.declared_classes.keys():
                # Type: ir.FunctionType = Type  <- Plus nécessaire, Type est maintenant la structure elle-même
                # ptr = self.builder.alloca(Type.return_type) <- Plus d'alloca
                # Storing the value to the pointer <- Plus de store
                # self.builder.store(value_, ptr)
                self.env.define(name, value_, Type) # On stocke la valeur, pas un pointeur!
            else:
                ptr = self.builder.alloca(Type)
                self.builder.store(value_, ptr)
                self.env.define(name, ptr, Type)
        else:
            ptr, _ = self.env.lookup(name)
            self.builder.store(value_, ptr)

        self.is_let = False
        self.let_node = None

    def visit_const_statement(self, node: ConstStatement) -> None:
        name: str = node.name.value
        value: Expression = node.value
        value_type: str = node.value_type

        value_, Type = self.resolve_value(node=value)
        const_var = ir.GlobalVariable(self.module, Type, name)
        const_var.initializer = ir.Constant(Type, value.value)
        const_var.global_constant = True

        if self.env.lookup(name) is None:
            self.env.define(name, const_var, Type)
        else:
            raise ValueError(f"Constant '{name}' already defined in the environment.")

    def visit_block_statement(self, node: BlockStatement) -> None:
        for stmt in node.statements:
            self.compile(stmt)

    def visit_return_statement(self, node: ReturnStatement) -> None:
        value: Expression = node.return_value
        value, Type = self.resolve_value(value)
        self.builder.ret(value)

    def visit_function_statement(self, node: FunctionStatement) -> None:
        name: str = node.name.value
        body: BlockStatement = node.body
        params: list[FunctionParameter] = node.parameters

        # Keep track of the names of each parameter
        param_names: list[str] = [p.name for p in params]

        # Keep track of the types for each parameter
        param_types: list[ir.Type] = [self.type_map[p.value_type] for p in params]

        return_type: ir.Type = self.type_map[node.return_type]

        fnty = ir.FunctionType(return_type, param_types)
        func = ir.Function(self.module, fnty, name=name)

        block: ir.Block = func.append_basic_block(f"{name}_entry")

        previous_builder = self.builder
        self.builder = ir.IRBuilder(block)

        # Storing the pointers to each parameter
        params_ptr = []
        for i, typ in enumerate(param_types):
            ptr = self.builder.alloca(typ)
            self.builder.store(func.args[i], ptr)
            params_ptr.append(ptr)

        # Adding the parameters to the environment
        previous_env = self.env
        self.env = Environment(parent=self.env)
        for i, x in enumerate(zip(param_types, param_names)):
            typ = param_types[i]
            ptr = params_ptr[i]

            self.env.define(x[1], ptr, typ)

        self.env.define(name, func, return_type)

        self.compile(body)

        if return_type == ir.VoidType():
            self.builder.ret_void()

        self.env = previous_env
        self.env.define(name, func, return_type)

        self.builder = previous_builder

    def visit_assign_statement(self, node: AssignStatement) -> None:
        name: str = node.ident.value
        operator: str = node.operator
        value: Expression = node.right_value

        if "." in name:
            class_instance_name, attribute_name = name.split(".")
            class_instance, Type = self.env.lookup(class_instance_name) # C'est la valeur, pas un pointeur
            # class_instance = self.builder.load(class_instance_ptr)  <- Plus besoin de charger!
            class_name = next((name for name, value_ in self.type_map.items() if value_ == Type)) # Type, pas Type.return_type

            attribute_index = None
            for i, field in enumerate(self.declared_classes[class_name]["fields"]):
                if field["name"] == attribute_name:
                    attribute_index = i

            # var_ptr = self.builder.extract_value(class_instance, attribute_index) # Plus un pointeur
            # orig_value = self.builder.load(var_ptr)
            orig_value = self.builder.extract_value(class_instance, attribute_index)  # Valeur directe


            right_value, right_type = self.resolve_value(value)

            if isinstance(orig_value.type, ir.IntType) and isinstance(right_type, ir.FloatType):
                orig_value = self.builder.sitofp(orig_value, ir.FloatType())
            if isinstance(orig_value.type, ir.FloatType) and isinstance(right_type, ir.IntType):
                right_value = self.builder.sitofp(right_value, ir.FloatType())

            value = None
            match operator:
                case '=':
                    value = right_value
                case '+=':
                    if isinstance(orig_value.type, ir.IntType) and isinstance(right_type, ir.IntType):
                        value = self.builder.add(orig_value, right_value)
                    else:
                        value = self.builder.fadd(orig_value, right_value)
                case '-=':
                    if isinstance(orig_value.type, ir.IntType) and isinstance(right_type, ir.IntType):
                        value = self.builder.sub(orig_value, right_value)
                    else:
                        value = self.builder.fsub(orig_value, right_value)
                case '*=':
                    if isinstance(orig_value.type, ir.IntType) and isinstance(right_type, ir.IntType):
                        value = self.builder.mul(orig_value, right_value)
                    else:
                        value = self.builder.fmul(orig_value, right_value)
                case '/=':
                    if isinstance(orig_value.type, ir.IntType) and isinstance(right_type, ir.IntType):
                        value = self.builder.sdiv(orig_value, right_value)
                    else:
                        value = self.builder.fdiv(orig_value, right_value)
                case _:
                    print("Unsupported Assignment Operator")

            # self.builder.insert_value(class_instance, value, attribute_index) # Pas besoin de stocker dans un pointeur
            updated_instance = self.builder.insert_value(class_instance, value, attribute_index) # Insère la nouvelle valeur
            self.env.define(class_instance_name, updated_instance, Type) # Et on remplace l'instance dans l'environment
        else:
            if self.env.lookup(name) is None:
                self.errors.append(f"[line {node.line_no}] COMPILE ERROR: Identifier {name} has not been declared before it was re-assigned.")
                return

            var_ptr, _ = self.env.lookup(name)
            orig_value = self.builder.load(var_ptr)

            right_value, right_type = self.resolve_value(value)

            if isinstance(orig_value.type, ir.IntType) and isinstance(right_type, ir.FloatType):
                orig_value = self.builder.sitofp(orig_value, ir.FloatType())
            if isinstance(orig_value.type, ir.FloatType) and isinstance(right_type, ir.IntType):
                right_value = self.builder.sitofp(right_value, ir.FloatType())

            value = None
            Type = None
            match operator:
                case '=':
                    value = right_value
                case '+=':
                    if isinstance(orig_value.type, ir.IntType) and isinstance(right_type, ir.IntType):
                        value = self.builder.add(orig_value, right_value)
                    else:
                        value = self.builder.fadd(orig_value, right_value)
                case '-=':
                    if isinstance(orig_value.type, ir.IntType) and isinstance(right_type, ir.IntType):
                        value = self.builder.sub(orig_value, right_value)
                    else:
                        value = self.builder.fsub(orig_value, right_value)
                case '*=':
                    if isinstance(orig_value.type, ir.IntType) and isinstance(right_type, ir.IntType):
                        value = self.builder.mul(orig_value, right_value)
                    else:
                        value = self.builder.fmul(orig_value, right_value)
                case '/=':
                    if isinstance(orig_value.type, ir.IntType) and isinstance(right_type, ir.IntType):
                        value = self.builder.sdiv(orig_value, right_value)
                    else:
                        value = self.builder.fdiv(orig_value, right_value)
                case _:
                    print("Unsupported Assignment Operator")

            ptr, _ = self.env.lookup(name)
            self.builder.store(value, ptr)

    def visit_if_statement(self, node: IfStatement) -> None:
        condition = node.condition
        consequence = node.consequence
        alternative = node.alternative

        test, Type = self.resolve_value(condition)

        # If there is no else block
        if alternative is None:
            with self.builder.if_then(test):
                self.compile(consequence)
        else:
            with self.builder.if_else(test) as (true, otherwise):
                # Creating a condition branch
                #      condition
                #        / \
                #     true  false
                #       /   \
                #      /     \
                # if block  else block
                with true:
                    self.compile(consequence)
                with otherwise:
                    self.compile(alternative)

    def visit_while_statement(self, node: WhileStatement) -> None:
        condition: Expression = node.condition
        body: BlockStatement = node.body

        test, _ = self.resolve_value(condition)

        # Entry block that runs if the condition is true
        while_loop_entry = self.builder.append_basic_block(f"while_loop_entry_{self.increment_counter()}")

        # If the condition is false, it runs from this block
        while_loop_otherwhise = self.builder.append_basic_block(f"while_loop_otherwise_{self.counter}")

        # Creating a condition branch
        #     condition
        #        / \
        # if true   if false
        #       /   \
        #      /     \
        # true block  false block
        self.builder.cbranch(test, while_loop_entry, while_loop_otherwhise)

        # Setting the builder position-at-start
        self.builder.position_at_start(while_loop_entry)

        # Compile the body of the while statement
        self.compile(body)

        test, _ = self.resolve_value(condition)

        self.builder.cbranch(test, while_loop_entry, while_loop_otherwhise)
        self.builder.position_at_start(while_loop_otherwhise)

    def visit_break_statement(self, node: BreakStatement) -> None:
        self.builder.branch(self.breakpoints[-1])

    def visit_continue_statement(self, node: ContinueStatement) -> None:
        self.builder.branch(self.continues[-1])

    def visit_for_statement(self, node: ForStatement) -> None:
        var_declaration: LetStatement = node.var_declaration
        condition: Expression = node.condition
        action: AssignStatement = node.action
        body: BlockStatement = node.body

        # Creating a new environment specifically for the for statement
        previous_env = self.env
        self.env = Environment(parent=previous_env)

        # compile the let statement
        self.compile(var_declaration)

        for_loop_entry = self.builder.append_basic_block(f"for_loop_entry_{self.increment_counter()}")
        for_loop_otherwise = self.builder.append_basic_block(f"for_loop_otherwise_{self.counter}")

        self.breakpoints.append(for_loop_otherwise)
        self.continues.append(for_loop_entry)

        self.builder.branch(for_loop_entry)
        self.builder.position_at_start(for_loop_entry)

        self.compile(body)

        self.compile(action)

        test, _ = self.resolve_value(condition)

        self.builder.cbranch(test, for_loop_entry, for_loop_otherwise)

        self.builder.position_at_start(for_loop_otherwise)

        self.breakpoints.pop()
        self.continues.pop()

    def visit_import_statement(self, node: ImportStatement) -> None:
        file_path: str = node.file_path

        if self.global_parsed_pallets.get(file_path) is not None:
            # print(f"[Billie Warning] {file_path} is already imported globally\n")
            return
        
        abs_file_path = ""
        if os.path.exists(f"{settings.STDLIB_PATH}/{file_path}.billie"):
            abs_file_path = f"{settings.STDLIB_PATH}/{file_path}.billie"
        elif os.path.exists(f"{settings.MODULES_PATH}/{file_path}.billie"):
            abs_file_path = f"{settings.MODULES_PATH}/{file_path}.billie"
        elif os.path.exists(f"{os.path.dirname(os.path.abspath(settings.ENTRY_FILE))}/{file_path}.billie"):
            abs_file_path = f"{os.path.dirname(os.path.abspath(settings.ENTRY_FILE))}/{file_path}.billie"
        else:
            raise FileNotFoundError(f"{file_path}.billie not found.")

        with open(abs_file_path, "r") as f:
            pallet_code: str = f.read()

        l = Lexer(source=pallet_code)
        p = Parser(lexer=l)

        program: Program = p.parse_program()
        if len(p.errors) > 0:
            print(f"[line {node.line_no}] Error with imported pallet: {file_path}")
            for err in p.errors:
                print(err)
            exit(1)

        self.compile(node=program)

        self.global_parsed_pallets[file_path] = program

    def visit_method_statement(self, node: MethodClassStatement, class_type: ir.IdentifiedStructType) -> None:
        name: str = node.name.value
        body: BlockStatement = node.body
        params: list[FunctionParameter] = node.parameters

        # Keep track of the names of each parameter
        param_names: list[str] = ["self"] + [p.name for p in params]

        # Keep track of the types for each parameter
        param_types: list[ir.Type] = [class_type] + [self.type_map[p.value_type] for p in params]

        return_type: ir.Type = self.type_map[node.return_type]

        fnty = ir.FunctionType(return_type, param_types)
        func = ir.Function(self.module, fnty, name=f"{class_type.name}_{name}")

        block: ir.Block = func.append_basic_block(f"{class_type.name}_{name}_entry")

        previous_builder = self.builder
        self.builder = ir.IRBuilder(block)

        previous_env = self.env
        self.env = Environment(parent=self.env)
        self.env.define("self", func.args[0], class_type)

        # Storing the pointers to each parameter
        params_ptr = []
        for i, typ in enumerate(param_types[1:]):
            ptr = self.builder.alloca(typ)
            self.builder.store(func.args[i + 1], ptr)
            params_ptr.append(ptr)

        # Adding the parameters to the environment
        for i, x in enumerate(param_names[1:]):
            self.env.define(x, params_ptr[i], param_types[i + 1])

        self.env.define(f"{class_type.name}_{name}", func, return_type)

        self.compile(body)

        if return_type == ir.VoidType():
            self.builder.ret_void()

        self.env = previous_env
        self.env.define(f"{class_type.name}_{name}", func, return_type)

        self.builder = previous_builder

    def visit_class_statement(self, node: ClassStatement) -> None:
            class_name = node.name.value
            fields = node.fields
            methods = node.methods

            # Création du type de classe
            class_type = self.module.context.get_identified_type(class_name)
            class_type.set_body(
                *[self.type_map[field.value_type] for field in fields]
            )

            self.type_map[class_name] = class_type
            self.declared_classes[class_name] = {
                "fields": [
                    {
                        "name": field.name.value,
                        "type": self.type_map[field.value_type]
                    } for field in fields
                ]
            }

            for method in methods:
                self.visit_method_statement(method, class_type)

            # Si la classe n'a pas de constructeur init
            if not any(method.name.value == "init" for method in methods):  # Check for "init" correctly
                # Modifier ici : Retourner directement l'instance au lieu d'un pointeur
                func_type = ir.FunctionType(class_type, [])  # ⬅️ Retourne une instance
                func = ir.Function(self.module, func_type, name=f"{class_name}_init")
                self.env.define(f"{class_name}_init", func, class_type)  # Stocker le FunctionType

                # Création du bloc d'entrée
                block = func.append_basic_block(name=f"{class_name}_init_entry")
                previous_builder = self.builder
                self.builder = ir.IRBuilder(block)

                previous_env = self.env
                self.env = Environment(parent=self.env)

                # Initialiser une structure vide
                instance = ir.Constant(class_type, None)  # ⬅️ Instance vide
                for i, field in enumerate(fields):
                    field_type = self.type_map[field.value_type]
                    if isinstance(field_type, ir.FloatType):
                        default_value = ir.Constant(field_type, float(field_type.null))
                    else:
                        default_value = ir.Constant(field_type, field_type.null)
                    instance = self.builder.insert_value(instance, default_value, i)

                # Retourner directement la structure complète
                self.builder.ret(instance)

                # Rétablir le contexte
                self.builder = previous_builder
                self.env = previous_env
    # endregion

    # region Visit Expressions Methods
    def visit_infix_expression(self, node: InfixExpression) -> tuple[ir.Value, ir.Type]:
        operator: str = node.operator
        left_value, left_type = self.resolve_value(node.left_node)
        right_value, right_type = self.resolve_value(node.right_node)

        value = None
        Type = None
        
        # Gestion des opérateurs logiques
        if operator == '||':
            value = self.builder.or_(left_value, right_value)
        elif operator == '&&':
            value = self.builder.and_(left_value, right_value)
        
        # Gestion des opérations arithmétiques et comparaisons
        else:
            is_left_float = isinstance(left_type, ir.FloatType)
            is_right_float = isinstance(right_type, ir.FloatType)
            is_left_int = isinstance(left_type, ir.IntType)
            is_right_int = isinstance(right_type, ir.IntType)
            
            # Upcast des int en float si nécessaire
            if is_left_int and is_right_float:
                left_value = self.builder.sitofp(left_value, right_type)
                left_type = right_type
            elif is_right_int and is_left_float:
                right_value = self.builder.sitofp(right_value, left_type)
                right_type = left_type
            
            if isinstance(left_type, ir.IntType) and isinstance(right_type, ir.IntType):
                Type = self.type_map['int']
                match operator:
                    case '+': value = self.builder.add(left_value, right_value)
                    case '-': value = self.builder.sub(left_value, right_value)
                    case '*': value = self.builder.mul(left_value, right_value)
                    case '/': value = self.builder.sdiv(left_value, right_value)
                    case '%': value = self.builder.srem(left_value, right_value)
                    case '<': value = self.builder.icmp_signed('<', left_value, right_value)
                    case '<=': value = self.builder.icmp_signed('<=', left_value, right_value)
                    case '>': value = self.builder.icmp_signed('>', left_value, right_value)
                    case '>=': value = self.builder.icmp_signed('>=', left_value, right_value)
                    case '==': value = self.builder.icmp_signed('==', left_value, right_value)
                if operator in ('<', '<=', '>', '>=', '=='):
                    Type = ir.IntType(1)
            
            elif isinstance(left_type, ir.FloatType) and isinstance(right_type, ir.FloatType):
                Type = ir.FloatType()
                match operator:
                    case '+': value = self.builder.fadd(left_value, right_value)
                    case '-': value = self.builder.fsub(left_value, right_value)
                    case '*': value = self.builder.fmul(left_value, right_value)
                    case '/': value = self.builder.fdiv(left_value, right_value)
                    case '%': value = self.builder.frem(left_value, right_value)
                    case '<': value = self.builder.fcmp_ordered('<', left_value, right_value)
                    case '<=': value = self.builder.fcmp_ordered('<=', left_value, right_value)
                    case '>': value = self.builder.fcmp_ordered('>', left_value, right_value)
                    case '>=': value = self.builder.fcmp_ordered('>=', left_value, right_value)
                    case '==': value = self.builder.fcmp_ordered('==', left_value, right_value)
                if operator in ('<', '<=', '>', '>=', '=='):
                    Type = ir.IntType(1)
            
        return value, Type

    def visit_call_expression(self, node: CallExpression) -> tuple[ir.Instruction, ir.Type]:
        name: str = node.function.value
        params: list[Expression] = node.arguments

        args = []
        types = []
        if len(params) > 0:
            for x in params:
                p_val, p_type = self.resolve_value(x)
                args.append(p_val)
                types.append(p_type)

        if name == "print":
            ret = self.builtin_printf(params=args, return_type=types[0])
            ret_type = self.type_map['int']
        elif name == "init":
            if self.is_let and not self.let_node is None:
                func_name = f"{self.let_node.value_type}_init"
                func, ret_type = self.env.lookup(func_name)
                ret = self.builder.call(func, args)
        elif "." in name:
            class_instance, class_method = name.split(".")
            data = self.env.lookup(class_instance)
            if data is None:
                self.errors.append(f"[line {node.line_no}] COMPILE ERROR: Identifier {name} is not defined.")
                return
            value, Type = data
            class_name = next((name for name, value_ in self.type_map.items() if value_ == Type))
            class_method_name = f"{class_name}_{class_method}"
            func, ret_type = self.env.lookup(class_method_name)
            args = [value] + args
            ret = self.builder.call(func, args)
        else:
            func, ret_type = self.env.lookup(name)
            ret = self.builder.call(func, args)

        return ret, ret_type
    
    def visit_prefix_expression(self, node: PrefixExpression) -> tuple[ir.Value, ir.Type]:
        operator: str = node.operator
        right_node: Expression = node.right_node

        right_value, right_type = self.resolve_value(right_node)

        Type = None
        value = None
        if isinstance(right_type, ir.FloatType):
            Type = ir.FloatType()
            match operator:
                case '-':
                    value = self.builder.fmul(right_value, ir.Constant(ir.FloatType(), -1.0))
                case '!':
                    value = ir.Constant(ir.IntType(1), 0)
        elif isinstance(right_type, ir.IntType):
            Type = ir.IntType(32)
            match operator:
                case '-':
                    value = self.builder.mul(right_value, ir.Constant(ir.IntType(64), -1))
                case '!':
                    value = self.builder.not_(right_value)

        return value, Type
    
    def visit_postfix_expression(self, node: PostfixExpression) -> None:
        left_node: IdentifierLiteral = node.left_node
        operator: str = node.operator

        if self.env.lookup(left_node.value) is None:
            self.errors.append(f"[line {node.line_no}] COMPILE ERROR: Identifier {left_node.value} has not been declared before it was used in a PostfixExpression.")
            return
        
        var_ptr, _ = self.env.lookup(left_node.value)
        orig_value = self.builder.load(var_ptr)

        value = None
        match operator:
            case "++":
                if isinstance(orig_value.type, ir.IntType):
                    value = self.builder.add(orig_value, ir.Constant(ir.IntType(64), 1))
                elif isinstance(orig_value.type, ir.FloatType):
                    value = self.builder.fadd(orig_value, ir.Constant(ir.FloatType(), 1.0))
            case "--":
                if isinstance(orig_value.type, ir.IntType):
                    value = self.builder.sub(orig_value, ir.Constant(ir.IntType(64), 1))
                elif isinstance(orig_value.type, ir.FloatType):
                    value = self.builder.fsub(orig_value, ir.Constant(ir.FloatType(), 1.0))

        self.builder.store(value, var_ptr)
    # endregion Visit Expression Methods

    # region Helper Methods
    def resolve_value(self, node: Expression, value_type: str = None) -> tuple[ir.Value, ir.Type]:
        """ Resolves a value and returns a tuple (ir_value, ir_type) """
        match node.type():
            # Literals
            case NodeType.IntegerLiteral:
                node: IntegerLiteral = node
                value, Type = node.value, self.type_map['int' if value_type is None else value_type]
                return ir.Constant(Type, value), Type
            case NodeType.FloatLiteral:
                node: FloatLiteral = node
                value, Type = node.value, self.type_map['float' if value_type is None else value_type]
                return ir.Constant(Type, value), Type
            case NodeType.IdentifierLiteral:
                node: IdentifierLiteral = node
                if "." in node.value:
                    class_instance_name, attribute_name = node.value.split(".")
                    class_instance, Type = self.env.lookup(class_instance_name)
                    class_name = next((name for name, value_ in self.type_map.items() if value_ == Type))

                    attribute_index = None
                    for i, field in enumerate(self.declared_classes[class_name]["fields"]):
                        if field["name"] == attribute_name:
                            attribute_index = i

                    # attribute_ptr = self.builder.extract_value(class_instance, attribute_index)
                    # attribute_value = self.builder.load(attribute_ptr)
                    attribute_value = self.builder.extract_value(class_instance, attribute_index)

                    attribute_type = None
                    for field in self.declared_classes[class_name]["fields"]:
                        if field["name"] == attribute_name:
                            attribute_type = field["type"]

                    return attribute_value, attribute_type
                else:
                    data = self.env.lookup(node.value)
                    if data is None:
                        print(f"[line {node.line_no}] {node.value} is not defined.")
                        sys.exit()
                    ptr, Type = data

                    if isinstance(Type, ir.IdentifiedStructType): # Si c'est une classe
                        return ptr, Type  # Retourner la valeur directement, pas un pointeur
                    else:
                        return self.builder.load(ptr), Type
            case NodeType.BooleanLiteral:
                node: BooleanLiteral = node
                return ir.Constant(ir.IntType(1), 1 if node.value else 0), ir.IntType(1)
            case NodeType.StringLiteral:
                node: StringLiteral = node
                string, Type = self.convert_string(node.value)
                return string, Type

            # Expression Values
            case NodeType.InfixExpression:
                return self.visit_infix_expression(node)
            case NodeType.CallExpression:
                return self.visit_call_expression(node)
            case NodeType.PrefixExpression:
                return self.visit_prefix_expression(node)

    def convert_string(self, string: str) -> tuple[ir.Constant, ir.PointerType]:
        string = string.replace('\\n', '\n\0')

        fmt = f"{string}\0"
        c_fmt = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt)), bytearray(fmt.encode("utf-8")))

        # Make the global variable for the string
        global_fmt = ir.GlobalVariable(self.module, c_fmt.type, name=f'__str_{self.increment_counter()}')
        global_fmt.linkage = 'internal'
        global_fmt.global_constant = True
        global_fmt.initializer = c_fmt

        # Create a pointer to the first element of the string
        zero = ir.Constant(ir.IntType(32), 0)
        ptr = self.builder.gep(global_fmt, [zero, zero])

        return ptr, ir.PointerType(ir.IntType(8))

    def builtin_printf(self, params: list[ir.Instruction], return_type: ir.Type) -> None:
        """ Basic C builtin printf with float support """
        func, _ = self.env.lookup('print')

        c_str = self.builder.alloca(return_type)
        self.builder.store(params[0], c_str)

        rest_params = []
        for param in params[1:]:
            if isinstance(param.type, ir.FloatType):
                # Convertit le float en double pour printf
                param = self.builder.fpext(param, ir.DoubleType())
            rest_params.append(param)

        if isinstance(params[0], ir.LoadInstr):
            """ Printing from a variable load instruction """
            c_fmt: ir.LoadInstr = params[0]
            g_var_ptr = c_fmt.operands[0]
            string_val = self.builder.load(g_var_ptr)
            fmt_arg = self.builder.bitcast(string_val, ir.IntType(8).as_pointer())
            return self.builder.call(func, [fmt_arg, *rest_params])
        else:
            """ Printing from a normal string declared within printf """
            fmt_arg = self.builder.bitcast(self.module.get_global(f"__str_{self.counter}"), ir.IntType(8).as_pointer())
            return self.builder.call(func, [fmt_arg, *rest_params])
    # endregion Helper Methods
    