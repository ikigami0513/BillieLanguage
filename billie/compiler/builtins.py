from llvmlite import ir
from billie.compiler.types import TYPE_MAP
from billie.environment import Environment


# region printf function

def init_print(module: ir.Module) -> ir.Function:
    fnty: ir.FunctionType = ir.FunctionType(
        TYPE_MAP['int'],
        [ir.IntType(8).as_pointer()],
        var_arg=True
    )
    return ir.Function(module, fnty, 'printf')


def builtin_printf(env: Environment, builder: ir.IRBuilder, module: ir.Module, counter: int, params: list[ir.Instruction], return_type: ir.Type) -> None:
    func, _ = env.lookup('print')

    c_str = builder.alloca(return_type)
    builder.store(params[0], c_str)

    rest_params = []
    for param in params[1:]:
        if isinstance(param.type, ir.FloatType):
            # Convert float to double for printf
            param = builder.fpext(param, ir.DoubleType())
        rest_params.append(param)

    if isinstance(params[0], ir.LoadInstr):
        # Printing from a variable load instruction
        c_fmt: ir.LoadInstr = params[0]
        g_var_ptr = c_fmt.operands[0]
        string_val = builder.load(g_var_ptr)
        fmt_arg = builder.bitcast(string_val, ir.IntType(8).as_pointer())
        return builder.call(func, [fmt_arg, *rest_params])
    else:
        # Printing from a normal string declared within printf
        fmt_arg = builder.bitcast(module.get_global(f"__str_{counter}"), ir.IntType(8).as_pointer())
        return builder.call(func, [fmt_arg, *rest_params])

# endregion printf function


# region scanf function
def init_scanf(module: ir.Module) -> ir.Function:
    fnty: ir.FunctionType = ir.FunctionType(
        TYPE_MAP['int'],
        [ir.IntType(8).as_pointer()],
        var_arg=True
    )
    return ir.Function(module, fnty, 'scanf')


def builtin_scanf(env: Environment, builder: ir.IRBuilder, module: ir.Module, counter: int, params: list[ir.Instruction]) -> None:
    func, _ = env.lookup('scan')

    fmt_arg = None
    if isinstance(params[0], ir.LoadInstr):
        # Scanning from a variable load instruction for the format string
        c_fmt: ir.LoadInstr = params[0]
        if isinstance(c_fmt.type, ir.PointerType) and isinstance(c_fmt.type.pointee, ir.ArrayType) and c_fmt.type.pointee.element == ir.IntType(8):
            g_var_ptr = c_fmt.operands[0]
            string_val = builder.load(g_var_ptr)
            fmt_arg = builder.bitcast(string_val, ir.IntType(8).as_pointer())
        else:
            raise ValueError("Format string for scan is not an i8*")
    else:
        fmt_arg = builder.bitcast(module.get_global(f"__str_{counter}"), ir.IntType(8).as_pointer())

    scan_args = []
    for i, param in enumerate(params[1:]):
        print(f"Param for scan: {param}, Type: {param.type}")
        scan_args.append(param) # Directly use the pointer to the variable

    builder.call(func, [fmt_arg, *scan_args])
# endregion scanf function


# region booleans
def init_booleans(module: ir.Module) -> tuple[ir.GlobalVariable, ir.GlobalVariable]:
    bool_type: ir.Type = TYPE_MAP['bool']

    true_var = ir.GlobalVariable(module, bool_type, 'true')
    true_var.initializer = ir.Constant(bool_type, 1)
    true_var.global_constant = True

    false_var = ir.GlobalVariable(module, bool_type, 'false')
    false_var.initializer = ir.Constant(bool_type, 0)
    false_var.global_constant = True

    return true_var, false_var
# endregion booleans
