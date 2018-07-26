from Redy.Magic.Classic import record
from .AST import AST

ConstString = str


class TokenMeta(type):
    def __getitem__(self, item):
        return self


@record
class Tokenizer(AST, metaclass=TokenMeta):
    name: ConstString
    value: ...  # maybe const string
    lineno: int
    colno: int
