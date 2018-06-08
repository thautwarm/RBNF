from .user_interface import *
from ..ParserC import Atom, Parser
from ..Tokenizer import Tokenizer
from typing import Callable, Iterator, Dict

__all__ = ['compile', 'ResultDescription']


class ZeroExp:
    _top_parser: Parser
    _lexer: Callable[[str], Iterator[Tokenizer]]
    _lang: Dict[str, Parser]
    ctx: dict

    def __init__(self, bnf_syntax: str, use: str): ...

    def match(self, text) -> ResultDescription: ...


def compile(bnf_syntax: str, use: str = None) -> ZeroExp: ...
