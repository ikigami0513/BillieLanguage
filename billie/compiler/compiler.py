from llvmlite import ir
import os
import sys
from typing import Any, Optional

from billie.compiler.types import TYPE_MAP
from billie.compiler import builtins

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
        self.env.define('print', builtins.init_print(self.module), ir.IntType(32))
        self.env.define('scan', builtins.init_scan(self.module), ir.IntType(32))
        
        true_var, false_var = builtins.init_booleans(self.module)
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
        
        value_type_ir = TYPE_MAP[node.value_type]

        if node.value_type in self.declared_classes.keys():
            value_, _ = self.resolve_value(node=value)
            if self.env.lookup(name) is None:
                self.env.define(name, value_, value_type_ir)
            else:
                ptr, _ = self.env.lookup(name)
                self.builder.store(value_, ptr)
        
        elif node.value_type == 'string':
            max_string_length = 256
            string_array_type = ir.ArrayType(ir.IntType(8), max_string_length)
            # Allouer un espace sur la pile pour le tableau de caractères
            buffer_ptr = self.builder.alloca(string_array_type, name=name)
            # Définir la variable dans l'environnement en tant que pointeur vers le tableau
            self.env.define(name, buffer_ptr, buffer_ptr.type)

            if isinstance(value, StringLiteral) and value.value:
                encoded_value = (value.value.encode('utf-8') + b'\0')[:max_string_length]
                initializer = ir.Constant(ir.ArrayType(ir.IntType(8), len(encoded_value)), bytearray(encoded_value))
                global_init = ir.GlobalVariable(self.module, initializer.type, name + "_init")
                global_init.initializer = initializer
                global_init.global_constant = True

                # Copier la chaîne de caractères dans le tampon alloué
                src_ptr = self.builder.bitcast(global_init, ir.PointerType(ir.IntType(8)))
                dst_ptr = self.builder.gep(buffer_ptr, [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 0)])
                
                # Utiliser la fonction memcpy de C pour une copie plus robuste
                init_memcpy = self.module.get_or_insert_function(ir.FunctionType(ir.VoidType(), [ir.IntType(8).as_pointer(), ir.IntType(8).as_pointer(), ir.IntType(32)]), name="memcpy")
                self.builder.call(init_memcpy, [dst_ptr, src_ptr, ir.Constant(ir.IntType(32), len(encoded_value))])
            
        else:
            value_, _ = self.resolve_value(node=value)
            ptr = self.builder.alloca(value_type_ir)
            self.builder.store(value_, ptr)
            self.env.define(name, ptr, value_type_ir)

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
        param_types: list[ir.Type] = [TYPE_MAP[p.value_type] for p in params]

        return_type: ir.Type = TYPE_MAP[node.return_type]

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
            
            data_lookup = self.env.lookup(class_instance_name)
            if data_lookup is None:
                self.errors.append(f"[line {node.line_no}] COMPILE ERROR: Class instance '{class_instance_name}' is not defined.")
                return

            class_instance, class_type = data_lookup

            if isinstance(class_instance, ir.AllocaInstr):
                class_instance = self.builder.load(class_instance)
            
            class_name = next((n for n, v in TYPE_MAP.items() if v == class_type), None)
            if class_name is None:
                self.errors.append(f"[line {node.line_no}] COMPILE ERROR: Class type for instance '{class_instance_name}' not found.")
                return
                
            attribute_index = None
            for i, field in enumerate(self.declared_classes[class_name]["fields"]):
                if field["name"] == attribute_name:
                    attribute_index = i
                    break

            if attribute_index is None:
                self.errors.append(f"[line {node.line_no}] COMPILE ERROR: Attribute '{attribute_name}' not found in class '{class_name}'.")
                return
                
            right_value, right_type = self.resolve_value(value)

            field_type_in_class = self.declared_classes[class_name]["fields"][attribute_index]["type"]

            if isinstance(field_type_in_class, ir.PointerType) and isinstance(field_type_in_class.pointee, ir.IntType):
                # Cas spécifique d'une chaîne de caractères (type i8*)
                if isinstance(right_type, ir.PointerType) and isinstance(right_type.pointee, ir.IntType):
                    value_to_assign = right_value
                elif isinstance(right_type, ir.ArrayType) and isinstance(right_type.element, ir.IntType):
                    # Si le type résolu est un tableau ([N x i8]), on le convertit en pointeur (i8*)
                    value_to_assign = self.builder.gep(right_value, [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 0)])
                else:
                    self.errors.append(f"[line {node.line_no}] COMPILE ERROR: Cannot assign type {right_type} to a string attribute.")
                    return
            else:
                # Gérer les autres types numériques
                orig_value = self.builder.extract_value(class_instance, attribute_index)
                if isinstance(orig_value.type, ir.IntType) and isinstance(right_type, ir.FloatType):
                    orig_value = self.builder.sitofp(orig_value, ir.FloatType())
                if isinstance(orig_value.type, ir.FloatType) and isinstance(right_type, ir.IntType):
                    right_value = self.builder.sitofp(right_value, ir.FloatType())
                
                value_to_assign = None
                if operator == '=':
                    value_to_assign = right_value
                elif operator == '+=':
                    if isinstance(orig_value.type, ir.IntType):
                        value_to_assign = self.builder.add(orig_value, right_value)
                    else:
                        value_to_assign = self.builder.fadd(orig_value, right_value)
                elif operator == '-=':
                    if isinstance(orig_value.type, ir.IntType):
                        value_to_assign = self.builder.sub(orig_value, right_value)
                    else:
                        value_to_assign = self.builder.fsub(orig_value, right_value)
                elif operator == '*=':
                    if isinstance(orig_value.type, ir.IntType):
                        value_to_assign = self.builder.mul(orig_value, right_value)
                    else:
                        value_to_assign = self.builder.fmul(orig_value, right_value)
                elif operator == '/=':
                    if isinstance(orig_value.type, ir.IntType):
                        value_to_assign = self.builder.sdiv(orig_value, right_value)
                    else:
                        value_to_assign = self.builder.fdiv(orig_value, right_value)
                else:
                    self.errors.append(f"Unsupported Assignment Operator: {operator}")
                    return

            updated_instance = self.builder.insert_value(class_instance, value_to_assign, attribute_index)
            self.env.define(class_instance_name, updated_instance, class_type)
        else:
            # Affectation de variables simples
            if self.env.lookup(name) is None:
                self.errors.append(f"[line {node.line_no}] COMPILE ERROR: Identifier {name} has not been declared before it was re-assigned.")
                return

            var_ptr, var_type = self.env.lookup(name)

            if isinstance(value, StringLiteral):
                # Pour les variables de chaîne, on copie le contenu
                if not isinstance(var_type.pointee, ir.ArrayType) or not isinstance(var_type.pointee.element, ir.IntType):
                    self.errors.append(f"[line {node.line_no}] COMPILE ERROR: Cannot assign a string to a non-string variable.")
                    return

                encoded_value = (value.value.encode('utf-8') + b'\0')[:var_type.pointee.count]
                initializer = ir.Constant(ir.ArrayType(ir.IntType(8), len(encoded_value)), bytearray(encoded_value))

                # Créer une variable globale pour la chaîne constante
                global_init = ir.GlobalVariable(self.module, initializer.type, f"__tmp_str_{self.increment_counter()}")
                global_init.initializer = initializer
                global_init.global_constant = True

                # Copier la chaîne globale vers la variable locale
                src_ptr = self.builder.bitcast(global_init, ir.PointerType(ir.IntType(8)))
                dst_ptr = self.builder.gep(var_ptr, [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 0)])
                
                init_memcpy = self.module.get_or_insert_function(ir.FunctionType(ir.VoidType(), [ir.IntType(8).as_pointer(), ir.IntType(8).as_pointer(), ir.IntType(32)]), name="memcpy")
                self.builder.call(init_memcpy, [dst_ptr, src_ptr, ir.Constant(ir.IntType(32), len(encoded_value))])
            else:
                # Gérer les autres types de variables simples
                orig_value = self.builder.load(var_ptr)
                right_value, right_type = self.resolve_value(value)

                if isinstance(orig_value.type, ir.IntType) and isinstance(right_type, ir.FloatType):
                    orig_value = self.builder.sitofp(orig_value, ir.FloatType())
                if isinstance(orig_value.type, ir.FloatType) and isinstance(right_type, ir.IntType):
                    right_value = self.builder.sitofp(right_value, ir.FloatType())

                value_to_store = None
                if operator == '=':
                    value_to_store = right_value
                elif operator == '+=':
                    if isinstance(orig_value.type, ir.IntType):
                        value_to_store = self.builder.add(orig_value, right_value)
                    else:
                        value_to_store = self.builder.fadd(orig_value, right_value)
                elif operator == '-=':
                    if isinstance(orig_value.type, ir.IntType):
                        value_to_store = self.builder.sub(orig_value, right_value)
                    else:
                        value_to_store = self.builder.fsub(orig_value, right_value)
                elif operator == '*=':
                    if isinstance(orig_value.type, ir.IntType):
                        value_to_store = self.builder.mul(orig_value, right_value)
                    else:
                        value_to_store = self.builder.fmul(orig_value, right_value)
                elif operator == '/=':
                    if isinstance(orig_value.type, ir.IntType):
                        value_to_store = self.builder.sdiv(orig_value, right_value)
                    else:
                        value_to_store = self.builder.fdiv(orig_value, right_value)
                else:
                    self.errors.append(f"Unsupported Assignment Operator: {operator}")
                    return

                self.builder.store(value_to_store, var_ptr)

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
        param_types: list[ir.Type] = [class_type] + [TYPE_MAP[p.value_type] for p in params]

        return_type: ir.Type = TYPE_MAP[node.return_type]

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
                *[TYPE_MAP[field.value_type] for field in fields]
            )

            TYPE_MAP[class_name] = class_type
            self.declared_classes[class_name] = {
                "fields": [
                    {
                        "name": field.name.value,
                        "type": TYPE_MAP[field.value_type]
                    } for field in fields
                ]
            }

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
                    field_type = TYPE_MAP[field.value_type]
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

            for method in methods:
                self.visit_method_statement(method, class_type)
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
                Type = TYPE_MAP['int']
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
        
        if name == "scan":
            fmt_arg, fmt_type = self.resolve_value(params[0])
            args.append(fmt_arg)
            types.append(fmt_type)

            for x in params[1:]:
                if not isinstance(x, IdentifierLiteral):
                    self.errors.append(f"[line {node.line_no}] COMPILE ERROR: scan requires a variable as an argument.")
                    return None, None
                
                # Récupérer le pointeur vers la variable
                p_val = self.get_pointer_to_local_variable(x.value)
                p_type = self.get_type_of_variable(x.value)
                
                # AJOUT DE LA LIGNE DE CODE POUR CONVERTIR LE POINTEUR
                if isinstance(p_type, ir.PointerType) and isinstance(p_type.pointee, ir.ArrayType):
                    # Bitcast le pointeur du tableau en un pointeur de caractère générique (i8*)
                    p_val = self.builder.bitcast(p_val, ir.PointerType(ir.IntType(8)))
                    p_type = ir.PointerType(ir.IntType(8))
                
                args.append(p_val)
                types.append(p_type)

            ret = builtins.builtin_scanf(
                env=self.env, builder=self.builder, module=self.module,
                counter=self.counter, params=args, return_type=types[0]
            )
            ret_type = TYPE_MAP['int']
            return ret, ret_type

        # Cas général pour les autres fonctions
        if len(params) > 0:
            for x in params:
                p_val, p_type = self.resolve_value(x)
                args.append(p_val)
                types.append(p_type)

        if name == "print":
            ret = builtins.builtin_printf(
                env=self.env, builder=self.builder, module=self.module, 
                counter=self.counter, params=args, return_type=types[0]
            )
            ret_type = TYPE_MAP['int']

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
                return None, None
            value, Type = data
            class_name = next((n for n, v in TYPE_MAP.items() if v == Type), None)
            class_method_name = f"{class_name}_{class_method}"
            func, ret_type = self.env.lookup(class_method_name)
            args = [value] + args
            ret = self.builder.call(func, args)
        else:
            func, ret_type = self.env.lookup(name)
            ret = self.builder.call(func, args)

        return ret, ret_type

    def get_pointer_to_local_variable(self, var_name: str) -> ir.Value:
        """Helper function to get the pointer to a local variable."""
        ptr, _ = self.env.lookup(var_name)
        return ptr

    def get_type_of_variable(self, var_name: str) -> ir.Type:
        """Helper function to get the type of a local variable."""
        _, var_type = self.env.lookup(var_name)
        return var_type
    
    def get_pointer_to_local_variable(self, var_name: str) -> ir.Value:
        """Helper function to get the pointer to a local variable."""
        ptr, _ = self.env.lookup(var_name)
        return ptr
    
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
    def get_pointer_to_local_variable(self, var_name: str) -> ir.Value:
        """Helper function to get the pointer to a local variable."""
        ptr, _ = self.env.lookup(var_name)
        return ptr

    def resolve_value(self, node: Expression, value_type: str = None) -> tuple[ir.Value, ir.Type]:
        """ Resolves a value and returns a tuple (ir_value, ir_type) """
        match node.type():
            # Literals
            case NodeType.IntegerLiteral:
                node: IntegerLiteral = node
                value, Type = node.value, TYPE_MAP['int' if value_type is None else value_type]
                return ir.Constant(Type, value), Type
            case NodeType.FloatLiteral:
                node: FloatLiteral = node
                value, Type = node.value, TYPE_MAP['float' if value_type is None else value_type]
                return ir.Constant(Type, value), Type
            case NodeType.IdentifierLiteral:
                node: IdentifierLiteral = node
                if "." in node.value:
                    class_instance_name, attribute_name = node.value.split(".")
                    class_instance, Type = self.env.lookup(class_instance_name)
                    class_name = next((name for name, value_ in TYPE_MAP.items() if value_ == Type))

                    attribute_index = None
                    for i, field in enumerate(self.declared_classes[class_name]["fields"]):
                        if field["name"] == attribute_name:
                            attribute_index = i

                    if isinstance(class_instance, ir.AllocaInstr):
                        attribute_value = self.builder.extract_value(self.builder.load(class_instance), attribute_index)
                    else:
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
                    
                    # Correction: si le type est un pointeur vers un tableau (string),
                    # il faut renvoyer le pointeur vers le premier élément du tableau
                    if isinstance(Type, ir.PointerType) and isinstance(Type.pointee, ir.ArrayType) and isinstance(Type.pointee.element, ir.IntType) and Type.pointee.element.width == 8:
                        return self.builder.gep(ptr, [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 0)]), ir.PointerType(ir.IntType(8))
                    
                    if isinstance(Type, ir.IdentifiedStructType):
                        return ptr, Type
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
    # endregion Helper Methods
    