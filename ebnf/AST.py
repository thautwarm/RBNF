from Redy.Typing import *
from .Tokenizer import Tokenizer


class AST(List[Union['AST', Tokenizer]]):
    __slots__ = ['name']

    def __init__(self, name: str):
        super(AST, self).__init__()
        self.name = name
