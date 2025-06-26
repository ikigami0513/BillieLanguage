from billie.lexer import Lexer
from billie.parser import Parser
from billie.compiler.compiler import Compiler
from billie.ast import Program
from billie import settings
import json
import time
import subprocess
from argparse import ArgumentParser, Namespace

from llvmlite import ir
import llvmlite.binding as llvm
from ctypes import CFUNCTYPE, c_int

def parse_arguments() -> Namespace:
    arg_parser = ArgumentParser(
        description="Billie v0.0.1-alpha"
    )
    # Required Arguments
    arg_parser.add_argument("action", type=str, help="")

    return arg_parser.parse_args()

def load_settings():
    with open("./settings.json") as f:
        settings_ = json.load(f)
    debug: dict[str, str] = settings_.get("debug", {})
    settings.DEBUG_FOLDER = debug.get("debug_folder", settings.DEBUG_FOLDER)
    settings.LEXER_DEBUG = debug.get("lexer", False)
    settings.PARSER_DEBUG = debug.get("parser", False)
    settings.COMPILER_DEBUG = debug.get("compiler", False)
    settings.STDLIB_PATH = settings_.get("stdlib_path", settings.STDLIB_PATH)
    settings.MODULES_PATH = settings_.get("modules_path", settings.MODULES_PATH)
    settings.ENTRY_FILE = settings_.get("entry_file", settings.ENTRY_FILE)
    settings.BUILD_FOLDER = settings_.get("build", {}).get("build_folder", settings.BUILD_FOLDER)

if __name__ == '__main__':
    args = parse_arguments()
    action: str = args.action

    if action == "run":
        load_settings()
    
        # Read from input file
        with open(settings.ENTRY_FILE, "r") as f:
            code: str = f.read()

        if settings.LEXER_DEBUG:
            print("===== LEXER DEBUG =====")
            debug_lex: Lexer = Lexer(source=code)
            while debug_lex.current_char is not None:
                print(debug_lex.next_token())

        l = Lexer(source=code)
        p = Parser(lexer=l)

        parse_st: float = time.time()
        program: Program = p.parse_program()
        parse_et: float = time.time()

        if len(p.errors) > 0:
            for err in p.errors:
                print(err)
            exit(1)

        if settings.PARSER_DEBUG:
            with open(f"{settings.DEBUG_FOLDER}/ast.json", "w") as f:
                json.dump(program.json(), f, indent=4)

        c = Compiler()

        compiler_st: float = time.time()
        c.compile(node=program)
        compiler_et: float = time.time()

        # Output steps
        module: ir.Module = c.module
        module.triple = llvm.get_default_triple()

        if settings.COMPILER_DEBUG:
            with open(f"{settings.DEBUG_FOLDER}/ir.ll", "w") as f:
                f.write(str(module))

        if len(c.errors) > 0:
            print(f"==== COMPILER ERRORS ====")
            for err in c.errors:
                print(err)
            exit(1)

        llvm.initialize()
        llvm.initialize_native_target()
        llvm.initialize_native_asmprinter()

        try:
            llvm_ir_parsed = llvm.parse_assembly(str(module))
            llvm_ir_parsed.verify()
        except Exception as e:
            print(e)
            raise

        target_machine = llvm.Target.from_default_triple().create_target_machine()

        engine = llvm.create_mcjit_compiler(llvm_ir_parsed, target_machine)
        engine.finalize_object()

        # Run the function with the name 'main'. This is the entry point function of the entire program
        entry = engine.get_function_address('main')
        cfunc = CFUNCTYPE(c_int)(entry)

        st = time.time()
        result = cfunc()
        et = time.time()

        print(f"\n=== Parsed in: {round((parse_et - parse_st) * 1000, 6)} ms. ===")
        print(f"=== Compiled in: {round((compiler_et - compiler_st) * 1000, 6)} ms. ===")
        print(f"=== Executed in {round((et - st) * 1000, 6)} ms. ===")

        print(f'\nProgram returned: {result}')
        
    elif action == "build":
        load_settings()

        # Read from input file
        with open(settings.ENTRY_FILE, "r") as f:
            code: str = f.read()

        l = Lexer(source=code)
        p = Parser(lexer=l)
        program: Program = p.parse_program()

        c = Compiler()
        c.compile(node=program)

        module: ir.Module = c.module
        module.triple = llvm.get_default_triple()

        llvm_ir_path = f"{settings.DEBUG_FOLDER}/ir.ll"
        with open(llvm_ir_path, "w") as f:
            f.write(str(module))

        obj_file = f"{settings.BUILD_FOLDER}/output.obj"
        subprocess.run(["llc", "-filetype=obj", llvm_ir_path, "-o", obj_file], check=True)

        exe_file = f"{settings.BUILD_FOLDER}/program.exe"
        subprocess.run(["clang", obj_file, "-o", exe_file], check=True)
