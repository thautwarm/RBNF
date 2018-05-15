from Redy.Magic.Classic import record
from .AST import AST

ConstString = str


@record
class Tokenizer(AST):
    name: ConstString
    value: str  # maybe const string
    lineno: int
    colno: int
