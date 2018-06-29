from Redy.Magic.Pattern import Pattern
from asdl import *
import operator
@Pattern
def visit(_):
    return type(_)


@visit.case(Numeric)
def visit(a: Numeric):
    return a.value


cases = {
        Op.Pow: operator.pow,
        Op.FloorDiv: operator.floordiv,
        Op.Div: operator.truediv,
        Op.Sub: operator.sub,
        Op.Mod: operator.mod,
        Op.Add: operator.add,
        Op.Mul: operator.mul
}


@visit.case(Bin)
def visit(a: Bin):
    return cases[a.op](visit(a.l), visit(a.r))


