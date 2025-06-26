from llvmlite import ir

TYPE_MAP: dict[str, ir.Type] = {
    'int': ir.IntType(64),
    'float': ir.FloatType(),
    'bool': ir.IntType(1),
    'void': ir.VoidType(),
    'string': ir.PointerType(ir.IntType(8))
}
