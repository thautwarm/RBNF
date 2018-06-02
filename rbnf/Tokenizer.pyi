from .AST import AST
from typing import NamedTuple
from typing import Union, Generic, TypeVar

ConstString = str
lit = Union[str, bytes]
T = TypeVar('T')


class Tokenizer(AST, NamedTuple, Generic[T]):
    name: ConstString
    value: T  # maybe const string
    lineno: int
    colno: int
